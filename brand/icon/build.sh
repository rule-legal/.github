#!/bin/zsh
set -e
W=${0:A:h}; S=~/.claude/skills/compose-app-icon/scripts
ICTOOL="$(dirname "$(xcode-select -p)")/Applications/Icon Composer.app/Contents/Executables/ictool"
mkdir -p $W/icons $W/renders
for d in $W/src/${~1:-[A-Z]-*}(/); do n=${d:t}
  args=(); for a in $(jq -r '[.groups[].layers[] | ."image-name"] | unique[]' $d/icon.json); do args+=(--asset $a=$d/$a); done
  (cd $S && uv run -q python create_icon.py --output $W/icons/$n.icon --icon $d/icon.json $args --force >/dev/null && uv run -q python validate_icon.py $W/icons/$n.icon)
  mkdir -p $W/renders/$n
  for r in Default Dark TintedLight TintedDark ClearLight ClearDark; do
    "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/$r.png --platform iOS --rendition $r --width 512 --height 512 --scale 1 --design-generation 27 >/dev/null || echo "RENDER FAILED $n $r"
  done
  "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/small64.png --platform iOS --rendition Default --width 64 --height 64 --scale 1 --design-generation 27 >/dev/null
  "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/small32.png --platform iOS --rendition Default --width 32 --height 32 --scale 1 --design-generation 27 >/dev/null
  "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/mac.png --platform macOS --rendition Default --width 1024 --height 1024 --scale 1 --design-generation 27 >/dev/null
  "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/mac-dark.png --platform macOS --rendition Dark --width 1024 --height 1024 --scale 1 --design-generation 27 >/dev/null
  "$ICTOOL" $W/icons/$n.icon --export-image --output-file $W/renders/$n/mac64.png --platform macOS --rendition Default --width 64 --height 64 --scale 1 --design-generation 27 >/dev/null
done
