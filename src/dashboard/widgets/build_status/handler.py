import subprocess
import os
import re

def get_build_status():
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
    )
    readme_path = os.path.join(project_root, 'README.md')

    phase = 'Unknown'
    task = 'Unknown'
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
            phase_match = re.search(r'<!--\s*current-phase:\s*(.*?)\s*-->', content)
            if phase_match: phase = phase_match.group(1)
            task_match = re.search(r'<!--\s*current-task:\s*(.*?)\s*-->', content)
            if task_match: task = task_match.group(1)
    except:
        pass

    commit_hash = ''
    commit_msg = ''
    try:
        result = subprocess.run(['git', 'log', '-1', '--pretty=format:%h %s (%cr)'], capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            parts = result.stdout.strip().split(' ', 2)
            commit_hash = parts[0] if len(parts) > 0 else ''
            commit_msg = parts[2] if len(parts) > 2 else ''
    except:
        pass

    return {
        'phase': phase,
        'current_task': task,
        'last_commit': f'{commit_hash} {commit_msg}'.strip()
    }