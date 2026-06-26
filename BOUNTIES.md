# Bounties and payout proof

This repository uses public pull request threads and Solana transaction links to keep contributor payouts auditable.

Scope: this page records bounty payouts that were confirmed in the PR threads during the first contributor wave. It is not a promise of future payments and it does not replace the acceptance criteria on each bounty issue.

## Paid contributor wave

| Contributor | PRs | Wallet | Payout proof |
| --- | --- | --- | --- |
| @JHON12091986 | [#41](https://github.com/codegraphtheory/hermes-profile-template/pull/41) | `Agb7LtU4b6SNFSGzdNZ2CAykKifBSyTm5PCFYjBmW7sh` | [Solscan tx](https://solscan.io/tx/4YBgxSMtULBVd17e71oc9BfH6zg4QWsJzMf9Q1xr1ujuRnu5JCjAdLu6ZxsijKXuUVBH2E9jLqcy5BD8CXM7ek6q) |
| @leo-guinan | [#40](https://github.com/codegraphtheory/hermes-profile-template/pull/40), [#37](https://github.com/codegraphtheory/hermes-profile-template/pull/37), [#51](https://github.com/codegraphtheory/hermes-profile-template/pull/51) | `FFAdvcr2CUPbaQSypK3c8WfQo3SuyBh5YKrtzZRSvg34` | [Solscan tx](https://solscan.io/tx/3qGbbxGr8pQLoup6wRDNHqDWkhaZFjqDMmQRSP2ZQ1XaVBYjkhCfcrmeSSFJ8uA5a4bfwVyRUsB91RGHyTe9ymE4) |
| @psukhopompos | [#34](https://github.com/codegraphtheory/hermes-profile-template/pull/34), [#29](https://github.com/codegraphtheory/hermes-profile-template/pull/29) | `9CRkSXNeWaUY1F9jd7hMkTGEb1iTAuhsPz8JoDn43Wjk` | [Solscan tx](https://solscan.io/tx/3bVQDcjfkZK1PnYNimRPWg4P8M5oMUi8D2Vfjd1CiW2yb7dDwvWWZ3SbRi1N5DrUtREMUYc1iwLb4g9FGLAyras6) |
| @therealsaitama0 | [#28](https://github.com/codegraphtheory/hermes-profile-template/pull/28), [#38](https://github.com/codegraphtheory/hermes-profile-template/pull/38), [#36](https://github.com/codegraphtheory/hermes-profile-template/pull/36), [#35](https://github.com/codegraphtheory/hermes-profile-template/pull/35), [#33](https://github.com/codegraphtheory/hermes-profile-template/pull/33), [#31](https://github.com/codegraphtheory/hermes-profile-template/pull/31), [#24](https://github.com/codegraphtheory/hermes-profile-template/pull/24) | `C64LcyGryk9CWtXGNMTz1FnbYsVe6vHHSaX9EdjVBMPT` | [Solscan tx](https://solscan.io/tx/ef28eJxaZ5QFVxwKNMetU66oMXoqrg2ranV7vDbzs2bnqe17N5GoWXUPhUPsCFmJSSZmuwXsirUc7jNgZCn6bL1) |
| @xNicky2k | [#47](https://github.com/codegraphtheory/hermes-profile-template/pull/47) | `HvUzii2Dt2WAErMQ1ade6d5qNDthu7nPF8BUZzh8AhgR` | [Solscan tx](https://solscan.io/tx/3KzDAKcMu4XbDgUNtKXLpwPAVwqcKMuBibBiYAxUT4xVVQZWVwJw6ie8PgveqKqgSgPEZFnW7beXX7g8asfKRQn1) |
| @iyeanur6-cyber | [#22](https://github.com/codegraphtheory/hermes-profile-template/pull/22) | `297hZrAVMi3rujS1vxSEbrD43ezfms7snkPHaTGaLeka` | [Solscan tx](https://solscan.io/tx/2njide2JKtwqGwhoiuUfS8wmn3aLqUG7Bpsisrfjo8ZZBVg9ynfYLhjevgfPf4i3BVfTUmw2eQbcreZMRySGWaiA) |

## Contributor credit

The contributor wave was consolidated into a maintainer-reviewed integration so the repo could keep code quality high while still preserving first-time contributor credit.

Merged integration: [#53](https://github.com/codegraphtheory/hermes-profile-template/pull/53)

Main commits:

- [`f9e7d88`](https://github.com/codegraphtheory/hermes-profile-template/commit/f9e7d88d1853cbb92d992a6b358e3bcb849c9b51): integrated the first-time contributor toolkit.
- [`a4f445b`](https://github.com/codegraphtheory/hermes-profile-template/commit/a4f445b19b9e4f336ed833ee9b2cf243d310157c): normalized co-author credit.

## How future bounties should be handled

1. Link the bounty issue in the PR body.
2. Include a Solana wallet address in the PR body before payout review.
3. Keep one PR scoped to one issue unless a maintainer asks for consolidation.
4. After payment, a maintainer should comment with the wallet and Solscan transaction link.
5. Update this file only after the transaction link is available.

## Contributor kindness checklist

Before claiming or opening a bounty PR, please reduce maintainer load by doing the small checks first:

1. Check the issue thread and open PR list for active work on the same issue.
2. If another PR already covers the issue, either review/test it or choose a different issue instead of adding a near-duplicate.
3. Keep claims specific: name the issue, the intended artifact, and your Solana wallet if the issue is bounty-eligible.
4. Keep implementation PRs narrow enough to review in one pass. Avoid bundling unrelated bounties unless a maintainer asks for consolidation.
5. Put exact verification commands in the PR body, including failures or intentionally skipped checks.
6. If your PR is superseded by a maintainer integration, leave it closed unless a maintainer asks for a follow-up. Credit and payout can still be recorded from the original thread.

This is not a gate. It is a courtesy protocol for a crowded bounty board.
