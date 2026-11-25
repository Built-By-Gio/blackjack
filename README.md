# blackjack

A blackjack simulation for studying strategy: a bot that tries to play every hand optimally against a dealer bot, with a bankroll. For each decision it computes the expected value of standing, hitting, doubling, splitting and surrendering from the exact cards left in the shoe (composition-dependent, using a with-replacement approximation). Before each round it computes the player's edge for the current shoe and sizes the bet with fractional Kelly. It is one Python file that uses only the standard library.

Built by Gio ([Built-By-Gio](https://github.com/Built-By-Gio)).

## Status (2026-11-25)

Working, and how that is known (all run on 2026-11-25):
- `python bj.py --help` lists the options below.
- The built-in check, `python bj.py --test 20000`, passed all three parts:
  ```
  check1 strategy: 30/30 match basic strategy
  check2 full-shoe edge=-0.00485 (expect about -0.004..-0.006)
  check3 monte-carlo engine EV=-0.00870 +/- 0.00799 (20000 hands), z=-0.48 vs analytic
  ```
  Check 1 compares 30 decisions against standard basic strategy, check 2 compares the full-shoe house edge to the expected range for these rules, and check 3 compares the simulated result of the game engine to the computed edge.
- A short session, `python bj.py --rounds 2000 --seed 1`, printed:
  ```
  rounds=2000 hands_bet=670 wagered=32091 start=10000 final=12667.00 profit=+2667.00 roi=+8.3107% max_drawdown=1475.00
  ```
  This is one short seeded run. It is far too small to show a long-run edge.

Limits:
- The expected values use a with-replacement approximation, not an exact without-replacement calculation.
- It is a simulation. It is not advice for real-money gambling.

## Rules simulated

6 decks (changeable), dealer stands on soft 17, dealer peeks for blackjack, blackjack pays 3:2, double after split allowed, late surrender, split once, split aces get one card each, 75% penetration before reshuffle (changeable). Insurance is taken only when the remaining shoe makes it profitable. By default the bot sits out rounds with a negative edge ("wonging out"); with `--no-wong` it bets the minimum instead.

## What you need

- Python 3 (run with Python 3.13). No packages to install.

## How to run

1. Download `bj.py` or clone this repo, and open a terminal in its folder.
2. Run a session: `python bj.py` (defaults: 20000 rounds, bankroll 10000, bets 10 to 1000, half Kelly).
3. Change the setup with options, for example: `python bj.py --rounds 2000 --seed 1 --verbose`
4. Run the self-check: `python bj.py --test 20000`

Options:

| Option | Default | Meaning |
|---|---|---|
| `--rounds` | 20000 | rounds to play (stops early if the bankroll drops below the minimum bet) |
| `--bank` | 10000 | starting bankroll |
| `--min` / `--max` | 10 / 1000 | table bet limits |
| `--kelly` | 0.5 | Kelly fraction used for bet sizing |
| `--no-wong` | off | bet the minimum at a negative edge instead of sitting out |
| `--decks` | 6 | decks in the shoe |
| `--pen` | 0.75 | fraction of the shoe dealt before reshuffling |
| `--seed` | none | random seed, for repeatable runs |
| `--verbose` | off | print every round that had a bet |
| `--test HANDS` | | run the self-check with this many simulated hands |

The session summary shows rounds played, hands bet, total wagered, start and final bankroll, profit, return on amount wagered, and the largest drawdown.

## Repo layout

```
bj.py   the whole simulation: strategy engine, edge calculation, shoe, game loop, self-check
```

## Roadmap / future plans

No plans are recorded yet.

## Credits and license

Written in plain Python with the standard library only.

This project is released under the MIT License. See `LICENSE`.
