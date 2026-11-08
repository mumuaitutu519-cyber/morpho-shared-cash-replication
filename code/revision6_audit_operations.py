"""Independently enumerate all facility operations, including no-operation cases.

Read-only offline replay. The collector's classification function is not called.
Official registry/signature metadata are shared; raw receipt events are the input.
"""
import json

import pandas as pd

from revision6_audit_results import ROOT, OUT, checked, uint
from revision4_collect_spark_cases import registry
from revision6_destination_operations import signatures
from fetch_ethereum_full import TRANSFER_TOPIC, ZERO_TOPIC


def audit(domain):
    operations_path = OUT/f'domain_{domain}_operations.csv'
    if not operations_path.exists():
        return {'status': 'INCOMPLETE_COLLECTION'}
    reg, sig = registry()[domain], signatures()
    proxy, usdc, psm = (reg[k] for k in ['ALM_PROXY', 'USDC', 'PSM3'])
    vault = reg.get('MORPHO_VAULT_SUSDC')
    topic = lambda address: '0x' + address[2:].rjust(64, '0')
    frame = pd.read_csv(OUT/f'domain_{domain}_matches.csv', dtype=str)
    assert frame.status.eq('exact_mint').all()
    actual = pd.read_csv(operations_path, dtype=str)
    transactions = pd.read_csv(OUT/f'domain_{domain}_operations_transactions.csv', dtype=str)
    assert len(transactions) == frame.destination_tx.nunique()
    assert set(transactions.destination_tx) == set(frame.destination_tx)
    actual_keys = [(r.destination_tx, int(r.operation_log)) for r in actual.itertuples()]
    assert len(actual_keys) == len(set(actual_keys))
    reported = {key: row for key, row in zip(actual_keys, actual.itertuples())}
    manifest = json.loads((OUT/f'domain_{domain}_receipts.json').read_text())
    files = {row['tx_hash']: row for row in manifest['items']}
    seen_keys, counts, amounts = set(), {}, {}
    with_deposit = with_withdrawal = neither = shares_checked = 0
    for row in transactions.itertuples():
        tx = row.destination_tx
        receipt = checked(files[tx])['response']['result']
        assert receipt['transactionHash'] == tx and int(receipt['status'], 16) == 1
        logs = sorted(receipt['logs'], key=lambda item: int(item['logIndex'], 16))
        native = [item for item in logs if item['address'] == usdc and item['topics'][0] == TRANSFER_TOPIC]
        arrivals = frame[frame.destination_tx.eq(tx)]
        mint_indices = list(arrivals.mint_log.astype(int))
        assert int(row.source_burns) == len(arrivals)
        assert int(row.source_micro_usdc) == sum(int(x) for x in arrivals.amount_micro_usdc)
        deposits = withdrawals = 0
        used_native, used_shares = set(), set()
        for event in logs:
            address, topics = event['address'], event['topics']
            if not topics:
                continue
            kind = None
            if address == psm and topics[1:] == [topic(usdc), topic(proxy), topic(proxy)]:
                if topics[0] == sig['Deposit(address,address,address,uint256,uint256)']:
                    kind = 'PSM deposit'
                elif topics[0] == sig['Withdraw(address,address,address,uint256,uint256)']:
                    kind = 'PSM withdrawal'
            if vault and address == vault:
                if topics == [sig['Deposit(address,address,uint256,uint256)'], topic(proxy), topic(proxy)]:
                    kind = 'Vault deposit'
                elif len(topics) == 4 and topics[0] == sig['Withdraw(address,address,address,uint256,uint256)'] and topics[2:] == [topic(proxy), topic(proxy)]:
                    kind = 'Vault withdrawal'
            if kind is None:
                continue
            index = int(event['logIndex'], 16)
            key = tx, index
            seen_keys.add(key)
            assert key in reported, 'An eligible facility event was omitted'
            saved = reported[key]
            raw = bytes.fromhex(event['data'][2:])
            assert len(raw) == 64
            amount, shares = uint(raw, 0), uint(raw, 32)
            assert amount > 0 and shares > 0
            assert saved.operation == kind and saved.facility == address
            assert int(saved.amount_micro_usdc) == amount and int(saved.share_base_units) == shares
            deposit = kind.endswith('deposit')
            sender, recipient = (proxy, address) if deposit else (address, proxy)
            candidates = [int(item['logIndex'], 16) for item in native
                          if item['topics'] == [TRANSFER_TOPIC, topic(sender), topic(recipient)]
                          and int(item['data'], 16) == amount
                          and int(item['logIndex'], 16) < index
                          and int(item['logIndex'], 16) not in used_native]
            assert candidates and saved.validated_native_transfer == 'True'
            payment = max(candidates)
            assert int(saved.native_transfer_log) == payment
            used_native.add(payment)
            assert (saved.after_first_frame_mint == 'True') == (payment > min(mint_indices))
            assert (saved.after_all_frame_mints == 'True') == (payment > max(mint_indices))
            if vault and address == vault:
                share_topics = ([TRANSFER_TOPIC, ZERO_TOPIC, topic(proxy)] if deposit
                                else [TRANSFER_TOPIC, topic(proxy), ZERO_TOPIC])
                share_logs = [int(item['logIndex'], 16) for item in logs
                              if item['address'] == vault and item['topics'] == share_topics
                              and int(item['data'], 16) == shares
                              and int(item['logIndex'], 16) < index
                              and int(item['logIndex'], 16) not in used_shares]
                assert share_logs, 'Vault share mint/burn does not match the facility event'
                used_shares.add(max(share_logs)); shares_checked += 1
            deposits += deposit; withdrawals += not deposit
            counts[kind] = counts.get(kind, 0) + 1
            amounts[kind] = amounts.get(kind, 0) + amount
        assert int(row.validated_deposits) == deposits and int(row.validated_withdrawals) == withdrawals
        assert int(row.operations_without_native_link) == 0
        with_deposit += deposits > 0; with_withdrawal += withdrawals > 0
        neither += deposits + withdrawals == 0
    assert seen_keys == set(reported), 'Extra or omitted facility classifications'
    summary = json.loads((OUT/f'domain_{domain}_operations_summary.json').read_text())
    assert summary['destination_transactions'] == len(transactions)
    assert summary['transactions_with_validated_deposit'] == with_deposit
    assert summary['transactions_with_validated_withdrawal'] == with_withdrawal
    assert summary['transactions_without_validated_operation'] == neither
    assert summary['unlinked_operations'] == 0
    for kind, value in summary['operations'].items():
        assert value['events'] == counts.get(kind, 0)
        assert int(value['amount_micro_usdc']) == amounts.get(kind, 0)
    return {'status': 'PASS', 'transactions': len(transactions),
            'facility_events': len(seen_keys), 'no_operation_transactions': neither,
            'vault_share_mints_or_burns_checked': shares_checked,
            'scope': 'All eligible raw facility events enumerated; native payments and vault shares replayed'}


if __name__ == '__main__':
    print(json.dumps({str(domain): audit(domain) for domain in [2, 3, 6, 10]}, indent=2))
