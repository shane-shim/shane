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

def send_discord_notification(message, status="info", bot_type="Combined"):
    """Discord로 알림 전송"""
    colors = {
        "success": 0x00ff00,
        "warning": 0xffff00,
        "error": 0xff0000,
        "info": 0x0080ff
    }
    
    icons = {
        "news": "🤖",
        "qna": "💬",
        "combined": "📊"
    }
    
    embed = {
        "title": f"{icons.get(bot_type.lower(), '📊')} Airflow {bot_type} 모니터링",
        "description": message,
        "color": colors.get(status, 0x0080ff),
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"Airflow {bot_type} Monitor"}
    }
    
    data = {"embeds": [embed]}
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json=data)
        return response.status_code == 204
    except Exception as e:
        print(f"Discord 전송 실패: {e}")
        return False

def comprehensive_system_check(**context):
    """전체 시스템 상태 체크"""
    issues = []
    
    # 크론탭 확인
    cron_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "sudo crontab -l | grep -E '(adaptive_news_bot|adaptive_qna_bot)' | wc -l"
    ]
    
    try:
        result = subprocess.run(cron_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            cron_count = int(result.stdout.strip())
            if cron_count < 2:
                issues.append("❌ 크론탭 설정이 누락되었습니다.")
        else:
            issues.append("❌ 크론탭 확인 실패")
    except Exception as e:
        issues.append(f"❌ 크론탭 확인 오류: {str(e)}")
    
    # 디스크 공간 확인
    disk_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "df -h /home | tail -1 | awk '{print $5}' | sed 's/%//'"
    ]
    
    try:
        result = subprocess.run(disk_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            disk_usage = int(result.stdout.strip())
            if disk_usage > 90:
                issues.append(f"⚠️ 디스크 사용률이 {disk_usage}%입니다.")
    except Exception as e:
        issues.append(f"❌ 디스크 확인 오류: {str(e)}")
    
    # Python 프로세스 확인
    process_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "ps aux | grep -E '(adaptive_news_bot|adaptive_qna_bot)' | grep -v grep | wc -l"
    ]
    
    try:
        result = subprocess.run(process_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            process_count = int(result.stdout.strip())
            if process_count > 2:
                issues.append(f"⚠️ 비정상적으로 많은 봇 프로세스가 실행 중입니다: {process_count}개")
    except Exception as e:
        issues.append(f"❌ 프로세스 확인 오류: {str(e)}")
    
    # 로그 파일 크기 확인
    log_size_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "find /home/nerdlab-datastudio-python -name '*cron.log' -size +100M | wc -l"
    ]
    
    try:
        result = subprocess.run(log_size_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            large_logs = int(result.stdout.strip())
            if large_logs > 0:
                issues.append(f"⚠️ 100MB 이상의 대용량 로그 파일이 {large_logs}개 있습니다.")
    except Exception as e:
        issues.append(f"❌ 로그 크기 확인 오류: {str(e)}")
    
    # 이슈가 있으면 Discord로 알림
    if issues:
        message = "**시스템 점검 결과**\\n" + "\\n".join(issues)
        send_discord_notification(message, status="warning", bot_type="Combined")
    
    return len(issues) == 0

def daily_report(**context):
    """일일 보고서 생성"""
    report_lines = ["**📊 일일 크롤링 봇 보고서**\\n"]
    
    # 뉴스봇 통계
    news_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        """grep '뉴스를 전송합니다' /home/nerdlab-datastudio-python/adaptive_news_cron.log | tail -7 | wc -l"""
    ]
    
    try:
        result = subprocess.run(news_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            news_count = int(result.stdout.strip())
            report_lines.append(f"📰 뉴스봇: 최근 7일간 {news_count}회 실행")
    except:
        report_lines.append("📰 뉴스봇: 통계 수집 실패")
    
    # Q&A봇 통계
    qna_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        """grep 'Q&A를 전송합니다' /home/nerdlab-datastudio-python/adaptive_qna_cron.log | tail -7 | wc -l"""
    ]
    
    try:
        result = subprocess.run(qna_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            qna_count = int(result.stdout.strip())
            report_lines.append(f"💬 Q&A봇: 최근 7일간 {qna_count}회 실행")
    except:
        report_lines.append("💬 Q&A봇: 통계 수집 실패")
    
    # 에러 통계
    error_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        """grep -i error /home/nerdlab-datastudio-python/*cron.log | tail -24h | wc -l"""
    ]
    
    try:
        result = subprocess.run(error_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            error_count = int(result.stdout.strip())
            if error_count > 0:
                report_lines.append(f"\\n⚠️ 최근 24시간 동안 {error_count}개의 오류 발생")
    except:
        pass
    
    # 보고서 전송
    report = "\\n".join(report_lines)
    send_discord_notification(report, status="info", bot_type="Daily Report")

# 통합 모니터링 DAG
default_args = {
    'owner': 'nerdlab',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 14, 0, 0),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 시스템 건강상태 체크 DAG (4시간마다)
system_health_dag = DAG(
    'system_health_check',
    default_args=default_args,
    description='전체 시스템 건강상태 체크',
    schedule_interval='0 */4 * * *',  # 4시간마다
    catchup=False,
    tags=['monitoring', 'system', 'health'],
)

system_check_task = PythonOperator(
    task_id='comprehensive_system_check',
    python_callable=comprehensive_system_check,
    dag=system_health_dag,
)

# 일일 보고서 DAG
daily_report_dag = DAG(
    'daily_bot_report',
    default_args=default_args,
    description='일일 크롤링 봇 보고서',
    schedule_interval='0 22 * * *',  # 매일 오후 10시
    catchup=False,
    tags=['monitoring', 'report', 'daily'],
)

report_task = PythonOperator(
    task_id='generate_daily_report',
    python_callable=daily_report,
    dag=daily_report_dag,
)

# 긴급 대응 DAG
emergency_dag = DAG(
    'emergency_bot_check',
    default_args=default_args,
    description='긴급 봇 상태 체크 및 복구',
    schedule_interval=None,  # 수동 트리거
    catchup=False,
    tags=['monitoring', 'emergency', 'manual'],
)

def emergency_restart_all(**context):
    """모든 봇 강제 재시작"""
    results = []
    
    # 뉴스봇 재시작
    news_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "cd /home/nerdlab-datastudio-python && /usr/bin/python3 /home/nerdlab-datastudio-python/src/adaptive_news_bot.py"
    ]
    
    try:
        result = subprocess.run(news_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            results.append("✅ 뉴스봇 재시작 성공")
        else:
            results.append(f"❌ 뉴스봇 재시작 실패: {result.stderr[:200]}")
    except Exception as e:
        results.append(f"❌ 뉴스봇 재시작 오류: {str(e)}")
    
    # Q&A봇 재시작
    qna_cmd = [
        "ssh", "-i", SSH_KEY, f"{SSH_USER}@{SSH_HOST}",
        "cd /home/nerdlab-datastudio-python && /usr/bin/python3 /home/nerdlab-datastudio-python/src/adaptive_qna_bot.py"
    ]
    
    try:
        result = subprocess.run(qna_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            results.append("✅ Q&A봇 재시작 성공")
        else:
            results.append(f"❌ Q&A봇 재시작 실패: {result.stderr[:200]}")
    except Exception as e:
        results.append(f"❌ Q&A봇 재시작 오류: {str(e)}")
    
    # 결과 알림
    message = "**🚨 긴급 재시작 결과**\\n" + "\\n".join(results)
    send_discord_notification(message, 
                            status="success" if all("✅" in r for r in results) else "error",
                            bot_type="Emergency")

emergency_restart_task = PythonOperator(
    task_id='emergency_restart_all_bots',
    python_callable=emergency_restart_all,
    dag=emergency_dag,
)