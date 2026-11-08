# Provider and state-boundary addendum

The original Tenderly public endpoint returned chain ID, one historical header and one historical maxWithdraw view. Its first transaction-index trace request returned HTTP 429 and collection there stopped. No later request will be sent to that endpoint.

The independently operated, publicly documented dRPC Base endpoint supports free read-only eth_call and block methods; its documentation reserves debug/trace and eth_getLogs for paid access. Those paid methods are excluded. The same historical maxWithdraw was reproduced there and the first deposit-equivalent request succeeded. Collection proceeds for the unchanged 94 events using deposit-block-end views and calls, in chronological order. No transaction-index replay is claimed. Original block receipts, complete block USDC transfer records and archived vault/market events will describe intervening operations. Later transactions can affect the observed state; same timestamp does not prove identical transaction-position state.

Sources: https://drpc.org/docs/base-api ; https://docs.base.org/base-chain/api-reference/ethereum-json-rpc-api/eth_call ; https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-debug . No paid subscription, authentication or broadcast.
