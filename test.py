import subprocess

command = 'echo penis'

print(subprocess.run(command, shell=True, capture_output=True))

