# Copyright 2019 Karol Horowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import subprocess
import sys

excluded_files = (
    "%s.py" % __file__,
    'install_compass',
)


def main(workspace_dir, dst_dir=None):
    workspace_dir = Path(workspace_dir)
    if not dst_dir:
        root_dir = workspace_dir / 'cmd'
    else:
        root_dir = Path(dst_dir)

    for i in workspace_dir.glob("**/bin/*"):
        if not i.is_file() or i.parts[-1] in excluded_files:
            continue
        relative_path = i.relative_to(workspace_dir)
        version = relative_path.parts[0]
        cmd = relative_path.parts[-1]

        cmd_dir = root_dir / cmd
        cmd_dir.mkdir(parents=True, exist_ok=True)

        cmd_version_out = cmd_dir / ('%s.out' % version)
        cmd_version_err = cmd_dir / ('%s.err' % version)
        with cmd_version_out.open("w") as out, cmd_version_err.open("w") as err:
            subprocess.run([str(i), '--help'], stdout=out, stderr=err)

        if cmd_version_out.stat().st_size == 0:
            cmd_version_out.unlink()

        if cmd_version_err.stat().st_size == 0:
            cmd_version_err.unlink()


if __name__ == '__main__':
    '''
        Tool for fetching help output from all commands in bin/ dir. 
        
        Usage:
        python cmds_help_output.py [workspace_dir]
        
        workspace_dir - directory where all mongo extracted packages are stored.
    '''
    if len(sys.argv) < 2:
        print("[workspace_dir] arg is required")

        exit(1)
    src_dir = sys.argv[1]
    output_dir = None
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    main(src_dir, output_dir)
