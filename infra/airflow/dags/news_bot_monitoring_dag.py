from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule
import requests
import json
import subprocess
import os

# Discord webhook URL
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1391310118850789436/OPWog1Noe8F08Vx19T6Q1TNgo7gMZT7HUQ2czDV-WZ8dhfDXKLmFOHhCM-Ydcbd4ikur"

# SSH 정보
SSH_KEY = "/Users/jaewansim/Desktop/nerdlab-datastudio-python/nerdlab_sshkey"
SSH_USER = "shane"
SSH_HOST = "34.22.78.151"

def send_discord_notification(message, status="info"):
    """Discord로 알림 전송"""
    colors = {
        "success": 0x00ff00,
        "warning": 0xffff00,
        "error": 0xff0000,
        "info": 0x0080ff
    }
    
    embed = {
        "title": "🤖 Airflow 뉴스봇 모니터링",
        "description": message,
        "color": colors.get(status, 0x0080ff),
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Airflow News Bot Monitor"}
    }
    
    data = {"embeds": [embed]}
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json=data)
        return response.status_code == 204
    except Exception as e:
        print(f"Discord 전송 실패: {e}")
        return False

def check_news_bot_log(**context):
    """뉴스봇 로그 확인"""
    # SSH로 원격 서버의 로그 확인
    cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "tail -50 /home/nerdlab-datastudio-python/adaptive_news_cron.log | grep -E '(완료|Error|error)'"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            log_content = result.stdout
            
            # 로그에서 성공/실패 확인
            if "적응형 뉴스 크롤링 완료" in log_content:
                # 최근 실행 시간 확인
                time_cmd = [
                    "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
                    "stat -c %Y /home/nerdlab-datastudio-python/adaptive_news_cron.log"
                ]
                time_result = subprocess.run(time_cmd, capture_output=True, text=True)
                
                if time_result.returncode == 0:
                    last_modified = int(time_result.stdout.strip())
                    current_time = int(datetime.now().timestamp())
                    time_diff = (current_time - last_modified) / 3600  # 시간 단위
                    
                    if time_diff < 2:  # 2시간 이내
                        print("뉴스봇이 정상적으로 실행되었습니다.")
                        return "success"
                    else:
                        print(f"뉴스봇이 {time_diff:.1f}시간 전에 마지막으로 실행되었습니다.")
                        return "warning"
            
            elif "Error" in log_content or "error" in log_content:
                print("뉴스봇 실행 중 오류 발생")
                context['task_instance'].xcom_push(key='error_log', value=log_content[-500:])
                return "error"
            else:
                print("뉴스봇 실행 확인 불가")
                return "unknown"
        else:
            print(f"로그 확인 실패: {result.stderr}")
            return "error"
            
    except Exception as e:
        print(f"로그 확인 중 오류: {str(e)}")
        return "error"

def run_news_bot_manually(**context):
    """뉴스봇 수동 실행"""
    cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "cd /home/nerdlab-datastudio-python && /usr/bin/python3 /home/nerdlab-datastudio-python/src/adaptive_news_bot.py"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            send_discord_notification(
                "✅ 뉴스봇이 Airflow에 의해 성공적으로 재실행되었습니다.",
                status="success"
            )
            return True
        else:
            send_discord_notification(
                f"❌ 뉴스봇 재실행 실패\\n```{result.stderr[-500:]}```",
                status="error"
            )
            return False
    except Exception as e:
        send_discord_notification(
            f"❌ 뉴스봇 실행 중 오류\\n```{str(e)}```",
            status="error"
        )
        return False

def check_and_notify(**context):
    """상태 확인 및 Discord 알림"""
    status = context['task_instance'].xcom_pull(task_ids='check_news_bot_log')
    
    if status == "error":
        error_log = context['task_instance'].xcom_pull(task_ids='check_news_bot_log', key='error_log')
        send_discord_notification(
            f"⚠️ 뉴스봇 오류 감지\\n```{error_log}```\\n재실행을 시도합니다...",
            status="warning"
        )
        return "needs_restart"
    elif status == "warning":
        send_discord_notification(
            "⚠️ 뉴스봇이 2시간 이상 실행되지 않았습니다. 재실행을 시도합니다...",
            status="warning"
        )
        return "needs_restart"
    elif status == "unknown":
        send_discord_notification(
            "❓ 뉴스봇 상태를 확인할 수 없습니다. 관리자 확인이 필요합니다.",
            status="warning"
        )
        return "unknown"
    else:
        # 성공 상태는 알림하지 않음 (스팸 방지)
        return "ok"

# DAG 정의
default_args = {
    'owner': 'nerdlab',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 14, 9, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'news_bot_monitoring',
    default_args=default_args,
    description='뉴스봇 모니터링 및 자동 재실행',
    schedule_interval='10 9 * * *',  # 매일 오전 9시 10분
    catchup=False,
    tags=['monitoring', 'news_bot'],
)

# Task 1: 뉴스봇 로그 확인
check_log_task = PythonOperator(
    task_id='check_news_bot_log',
    python_callable=check_news_bot_log,
    dag=dag,
)

# Task 2: 상태 확인 및 알림
notify_task = PythonOperator(
    task_id='check_and_notify',
    python_callable=check_and_notify,
    dag=dag,
)

# Task 3: 필요시 뉴스봇 재실행
restart_task = PythonOperator(
    task_id='restart_news_bot',
    python_callable=run_news_bot_manually,
    trigger_rule=TriggerRule.NONE_FAILED,
    dag=dag,
)

# Task 의존성 설정
check_log_task >> notify_task
notify_task >> restart_task

# 매시간 실행되는 상태 체크 DAG
hourly_dag = DAG(
    'news_bot_hourly_check',
    default_args=default_args,
    description='뉴스봇 시간별 상태 체크',
    schedule_interval='0 * * * *',  # 매시간
    catchup=False,
    tags=['monitoring', 'news_bot', 'hourly'],
)

def hourly_health_check(**context):
    """시간별 건강상태 체크"""
    cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "find /home/nerdlab-datastudio-python/adaptive_news_cron.log -mmin -1440 | wc -l"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip() == "0":
            # 24시간 이상 업데이트 없음
            send_discord_notification(
                "⚠️ 뉴스봇이 24시간 이상 업데이트되지 않았습니다.",
                status="warning"
            )
    except Exception as e:
        print(f"건강상태 체크 실패: {e}")

hourly_check_task = PythonOperator(
    task_id='hourly_health_check',
    python_callable=hourly_health_check,
    dag=hourly_dag,
)