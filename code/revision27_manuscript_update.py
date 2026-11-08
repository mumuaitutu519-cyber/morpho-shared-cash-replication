from pathlib import Path
import re,json,pandas as pd
T=Path(__file__).resolve().parents[1]/'submission/jifmim27/en';R=T.parents[2];O=R/'reports/revision27'
p=T/'body.tex';s=p.read_text()
a=s.index('The second large address is identified');b=s.index('\\subsection{Fixed-state capacity',a)
s=s[:a]+r'''\subsection{An independently named funding-to-claim comparison}
Ethena Labs' August 2025 attestation identifies the second large wallet as Coinbase Web3 Wallet 3 \citep{ethena2025}. A complete USDC ledger over blocks 34,450,000--34,758,680 contains seven incoming transfers and 15 subsequent vault deposits. Historical opening and ending wallet balances are both zero. All outgoing transfers are matched vault deposits, totaling 200,000,021 USDC. The ledger therefore closes without assigning an unexplained opening balance or ignoring competing departures.

Three immediate senders provide 151 million, 49 million and 21 USDC. Balance and order constraints identify each sender's total contribution to the deposit group, while individual deposit assignments can remain nonunique. All seven receipts contain ordinary USDC transfers and no accompanying bridge mint. This establishes the immediate wallet funding path; it does not establish the funds' fiat origin or the absence of upstream cross-chain operations at an intermediary.
\input{tables/ethena_funding}

Fourteen deposit-equivalent simulations succeed at block end. The first 5-USDC test deposit instead returns an insufficient-share-balance error: withdrawing exactly 5 USDC requires one more minimum share unit than the owner holds. Its converted claim and capacity are both 4.999999 USDC, and withdrawing that amount succeeds. The distinction matters for interpreting execution records: a share-rounding limit is not a market-cash shortfall. No provider error is included as a rejected withdrawal.

All 100 eligible daily opening states are independently checked for the owner's balance, converted claim and maximum withdrawal. Balances match the ledger exactly. Thirty-nine states have capacity below the full claim, none below a quarter, and minimum coverage is 41.38 percent. This independently named account extends the funding-to-claim application beyond Spark, but the funding channel differs. It is an informative comparison within the same vault, not an additional CCTP cohort or a representative sample of institutions.

The comparison also makes the same-transaction restriction economically visible. Large deposits can be financed through earlier wallet transfers, so a bundled-arrival method will not capture every institutional investment operation. Expanding the observation boundary requires a complete intervening ledger and verified opening cash, as supplied here; merely collecting deposits near an arrival would not suffice.

'''+s[b:]
s=s.replace('Inference clusters by owner and date.',r'Inference clusters by owner and date, addressing within-owner and common-date residual dependence \citep{petersen2009,cameron2011}.')
s=s.replace('The second named holder extends the ownership comparison but does not yet supply a verified independent cross-chain funding path.', 'The second named holder extends the funding-to-claim application through a different observed wallet-funding channel. Its upstream provenance remains outside the measured boundary.')
p.write_text(s)
(T/'tables/ethena_funding.tex').write_text(r'''\begin{table}[!htbp]\centering
\caption{Immediate funding and deposit-scale exits: the Ethena wallet}\label{tab:ethenafunding}
\begin{threeparttable}\setstretch{1}
\begin{tabular}{@{}p{10cm}r@{}}\toprule
Observed quantity & Amount / count \\\midrule
Opening USDC balance & 0 \\
Transfers from sender 0x6dcb...4467 (USDC) & 151,000,000 \\
Transfers from sender 0xb480...07fb (USDC) & 49,000,000 \\
Transfers from sender 0x1985...5c87 (USDC) & 21 \\
Total vault deposits (USDC) & 200,000,021 \\
Ending USDC balance & 0 \\
Incoming transfers / vault deposits & 7 / 15 \\
Deposit-equivalent execution successes & 14 \\
Insufficient-share-balance returns & 1 \\
Market-liquidity error returns & 0 \\\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\item \textit{Notes}. The complete fixed-window ledger covers blocks 34,450,000--34,758,680. All outgoing transfers are vault deposits. Joint first-use attribution of each immediate sender's funds equals its incoming total; individual source assignments need not be unique. Senders' full addresses, logs and optimization results accompany the data. The upstream economic origin of these funds is not inferred. Simulations use deposit block-end states. The one return is a one-share-unit rounding shortfall on the first 5-USDC deposit; withdrawing the available 4.999999 USDC succeeds.
\end{tablenotes}\end{threeparttable}\end{table}
''')
a=T/'appendix.tex';s=a.read_text();s+=r'''
\subsection{Extended-window funding and exact claims}
The independent-wallet source attribution uses the same nonnegative cash allocation constraints over a continuous multi-transaction ledger. The fixed window starts with an independently observed zero balance and ends with another observed zero balance. Seven incoming transfers and 15 outgoing vault deposits exhaust its USDC flows. Receipt checks authenticate all incoming transfers and deposit requests. Source-specific optimization produces joint totals of 151 million, 49 million and 21 USDC; event-level endpoints are retained separately and are not added to claim jointly attainable extrema. No bridge mint occurs in these incoming transactions. Earlier intermediary operations are not observed by this funding object.

For the owner panel, pending fee shares are reconstructed from the contract's last-total-assets state, current assets, supply and recorded fee. Integer conversions include virtual assets and shares. Reconstructed claims match direct Spark conversions on all 320 dates and direct Ethena conversions on all 100 dates. The 1-USDC main threshold retains exactly the same sample membership as the former ratio approximation. The positive-claim sensitivity now excludes shares whose converted value rounds to zero: its estimation sample is 948,755 observations. This is a unit correction, not a threshold selected from statistical significance. Original proxy-based estimates remain archived.

The delivered R26 evidence archive was separately extracted and its owner reconstruction, rate reconstruction, panel assembly and 224 coefficient records re-run in a clean directory. Maximum coefficient and p-value differences were $2.23\times10^{-13}$ and $9.44\times10^{-12}$ respectively. This validates retained-input portability in the same runtime; it is not a third-party historical recollection. The R27 inputs retain exact-claim corrections separately.
''';a.write_text(s)
r=T/'references.tex';s=r.read_text();entries=re.findall(r'(\\bibitem\[.*?)(?=\\bibitem\[|\\end\{thebibliography\})',s,flags=re.S)
def entry(tag,key,body,url):return r'\bibitem['+tag+r']{'+key+r'}\begin{minipage}[t]{\linewidth}\setlength{\parindent}{0pt}\hangindent=1.5em '+body+r'\par\url{'+url+r'}\par\end{minipage}\par'+'\n\n'
entries=[e for e in entries if '{ethena2025}' not in e]
entries += [entry('Cameron, Gelbach \\& Miller(2011)','cameron2011',r'Cameron, A. C., Gelbach, J. B. \& Miller, D. L. (2011). Robust inference with multiway clustering. \textit{Journal of Business \& Economic Statistics, 29}(2), 238--249.','https://doi.org/10.1198/jbes.2010.07136'),entry('Petersen(2009)','petersen2009',r'Petersen, M. A. (2009). Estimating standard errors in finance panel data sets: Comparing approaches. \textit{Review of Financial Studies, 22}(1), 435--480.','https://doi.org/10.1093/rfs/hhn053'),entry('Ethena Labs(2025)','ethena2025','Ethena Labs (2025). Custodian attestations of assets backing USDe: August. August 29. Accessed September 7, 2026.','https://paragraph.com/@ethena-labs/custodian-attestations-of-assets-backing-usde-august-2')]
r.write_text('\\begin{thebibliography}{99}\n'+''.join(sorted(entries,key=lambda x:x.split('[')[1].lower()))+'\\end{thebibliography}\n')
with (T/'references.bib').open('a') as f:f.write('\n@article{cameron2011,author={Cameron, A. Colin and Gelbach, Jonah B. and Miller, Douglas L.},year={2011},title={Robust Inference With Multiway Clustering},journal={Journal of Business & Economic Statistics},volume={29},number={2},pages={238--249},doi={10.1198/jbes.2010.07136}}\n@article{petersen2009,author={Petersen, Mitchell A.},year={2009},title={Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches},journal={Review of Financial Studies},volume={22},number={1},pages={435--480},doi={10.1093/rfs/hhn053}}\n')
