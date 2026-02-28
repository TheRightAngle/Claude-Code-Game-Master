#!/bin/bash
# dm-time.sh - Update campaign time (wrapper for time_manager.py)

source "$(dirname "$0")/common.sh"

if [ "$#" -lt 2 ]; then
    echo "Usage: dm-time.sh <time_of_day> <date>"
    echo "Example: dm-time.sh \"Dawn\" \"16th day of Harvestmoon, Year 1247\""
    exit 1
fi

require_active_campaign

TIME_OF_DAY="$1"
shift
DATE="$*"

dispatch_middleware "dm-time.sh" "$TIME_OF_DAY" "$DATE" && exit $?

(
    cd "$PROJECT_ROOT" || exit 1
    $PYTHON_CMD -m lib.time_manager update "$TIME_OF_DAY" "$DATE"
)
CORE_RC=$?
dispatch_middleware_post "dm-time.sh" "$TIME_OF_DAY" "$DATE"
exit $CORE_RC
