import time
import sys

def countdown(t):
    while t > 0:
        # divmod() calculates minutes and seconds from total seconds
        mins, secs = divmod(t, 60)
        # Format the time string
        timer_display = '{:02d}:{:02d}'.format(mins, secs)
        
        # Use carriage return to move cursor to the start of the line
        sys.stdout.write('\n Waiting for notifications...' + timer_display)
        # Manually flush the output buffer to ensure it prints immediately
        sys.stdout.flush()
        
        # Pause the script for 1 second
        time.sleep(1)
        # Decrease the time
        t -= 1

    # Overwrite the final line with "Complete!" and a newline character
    sys.stdout.write('\nComplete!      \n')

# Example usage: start a 10-second timer
# countdown(10)
