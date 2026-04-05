"""
Analyzer Module for DevTrackr - AI-Powered Performance Analysis

Uses Groq's fast LLM API to generate aggressive drill sergeant style
performance reviews based on commit data.
"""

from typing import Optional, List, Dict
from datetime import date, timedelta
import sys


def format_commit_summary(commits_data: List[Dict]) -> str:
    """
    Format commit data into a readable summary for the AI model.
    
    Args:
        commits_data: List of dicts with date, repo, and count keys
    
    Returns:
        Formatted string summarizing the commit activity
    """
    if not commits_data:
        return "No commits found in the last 7 days."
    
    total_commits = sum(c["count"] for c in commits_data)
    unique_repos = len(set(c["repo"] for c in commits_data))
    unique_days = len(set(c["date"] for c in commits_data))
    
    summary = f"""
COMMIT DATA SUMMARY (Last 7 Days):
- Total Commits: {total_commits}
- Unique Repositories: {unique_repos}
- Active Days: {unique_days}
- Commits Per Day Average: {total_commits / max(unique_days, 1):.1f}

BREAKDOWN BY DATE:
"""
    
    # Group by date
    by_date = {}
    for commit in commits_data:
        date_str = commit["date"]
        if date_str not in by_date:
            by_date[date_str] = {"count": 0, "repos": []}
        by_date[date_str]["count"] += commit["count"]
        by_date[date_str]["repos"].append(commit["repo"])
    
    # Format by date
    for date_str in sorted(by_date.keys(), reverse=True):
        data = by_date[date_str]
        summary += f"  {date_str}: {data['count']} commits across {len(set(data['repos']))} repos\n"
    
    return summary


def get_analysis_prompt(commits_data: List[Dict]) -> str:
    """
    Generate the prompt to send to Groq for analysis.
    
    Args:
        commits_data: List of commit records from database
    
    Returns:
        Formatted prompt for the AI model
    """
    summary = format_commit_summary(commits_data)
    
    prompt = f"""You are an aggressive, no-nonsense drill sergeant gym coach analyzing a developer's GitHub commit logs.

{summary}

Based on this developer's commit activity, provide a SHORT (2-3 sentences) AGGRESSIVE performance review in the style of a drill sergeant gym coach. Be funny, harsh, and motivational. Rate their performance. Use emojis but keep it brief.

Rules:
- Be aggressive and funny like a drill sergeant
- If commits are low: mock them for being lazy
- If commits are high: praise them like they're a beast
- Keep it to 2-3 sentences max
- Include relevant emojis
- Be encouraging but in a tough love way"""
    
    return prompt


def analyze_with_groq(commits_data: List[Dict], groq_client) -> Optional[str]:
    """
    Send commit data to Groq for AI analysis.
    
    Args:
        commits_data: List of commit records
        groq_client: Initialized Groq client
    
    Returns:
        AI-generated performance review string, or None if error
    """
    if not groq_client:
        print("No Groq client provided", file=sys.stderr)
        return None
    
    try:
        prompt = get_analysis_prompt(commits_data)
        print(f"[Groq] Sending prompt ({len(prompt)} chars) to Groq API", file=sys.stderr)
        
        message = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            max_tokens=256,
            temperature=0.8,  # Slightly higher for more personality
        )
        
        response_text = message.choices[0].message.content
        print(f"[Groq] Got response: {len(response_text)} chars", file=sys.stderr)
        return response_text
    
    except Exception as e:
        print(f"[Groq] Error: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def get_task_suggestions_prompt(commits_data: List[Dict], repo_names: List[str]) -> str:
    """
    Generate a prompt to ask Groq for coding task suggestions based on commit history and repos.
    
    Args:
        commits_data: List of dicts with date, repo, and count keys
        repo_names: List of repository names the developer works on
    
    Returns:
        Formatted prompt for the AI model
    """
    summary = format_commit_summary(commits_data)
    
    repos_str = ", ".join(repo_names) if repo_names else "various repositories"
    
    prompt = f"""You are a senior developer coach helping a dev plan their next day of work.

Based on this developer's recent commit activity:
{summary}

Repositories they work on: {repos_str}

Suggest EXACTLY 3 specific, actionable coding tasks they should do tomorrow.
Each task should be:
- Specific and concrete (not vague)
- Related to their recent work or repos
- Achievable in a dev session
- Written like a real Jira ticket

Format your response as EXACTLY 3 lines, one task per line.
No numbering, no extra text, just the 3 tasks.
Make them technical and real, like:
"Add comprehensive error handling to user authentication flow"
"Refactor database queries to reduce N+1 problems"
"Write unit tests for payment processing module"
"""
    
    return prompt


def get_task_suggestions(commits_data: List[Dict], repo_names: List[str], groq_client) -> Optional[List[str]]:
    """
    Get AI-generated task suggestions for tomorrow based on commit history.
    
    Args:
        commits_data: List of commit records from the database
        repo_names: List of repository names the developer works on
        groq_client: Initialized Groq client
    
    Returns:
        List of 3 task suggestion strings, or None if error
    """
    if not groq_client:
        print("[TaskSuggest] No Groq client provided", file=sys.stderr)
        return None
    
    try:
        prompt = get_task_suggestions_prompt(commits_data, repo_names)
        print(f"[TaskSuggest] Requesting suggestions from Groq", file=sys.stderr)
        
        message = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            max_tokens=512,
            temperature=0.7,
        )
        
        response_text = message.choices[0].message.content
        print(f"[TaskSuggest] Got response: {response_text[:100]}...", file=sys.stderr)
        
        # Parse the response into lines (tasks)
        lines = response_text.strip().split("\n")
        
        # Filter out empty lines and clean up
        tasks = [line.strip() for line in lines if line.strip()]
        
        # Take only the first 3 tasks
        tasks = tasks[:3]
        
        # Ensure we have exactly 3
        while len(tasks) < 3:
            tasks.append("Continue improving code quality and test coverage")
        
        print(f"[TaskSuggest] Extracted {len(tasks)} tasks", file=sys.stderr)
        return tasks
    
    except Exception as e:
        print(f"[TaskSuggest] Error: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None
