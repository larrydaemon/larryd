"""THE SWAP (SM2 agent035): the A to B switch set up correctly (the public name, its zone and record, both slots, the switch pointing
at one of them, the two secrets placed, read by name only), by the original's own check. It never swaps: the owner flips it on the swap
day, behind the PIN. Dry: the check is there and the command it would run (the check reads slot B, so a dry RUN does not run it)."""
import night

if __name__ == '__main__':
    night.main()
