# ==========================================
# 파일 위치 : moneypilot_back/app/services/admin_service.py
# 역할 : 관리자 계정 관련 비즈니스 로직
# 담당:
# 1. 관리자 계정 로그인
# 2. 사용자 사용량 및 비용 조회
# 3. 이용한도 조절
# ==========================================
from datetime import date
import psutil

from app.repositories.admin_repository import AdminRepository
    
class AdminService:
  def __init__(self, db):
    self.repository = AdminRepository(db)
    
  # ==========================================
  # 관리자 대시보드
  # ==========================================
  def get_dashboard(self):
      total_users = self.repository.count_users()
      today_tokens = self.repository.get_today_token_sum()
      today_cost = self.repository.get_today_cost()
      monthly_cost = self.repository.get_monthly_cost()
      total_cost = self.repository.get_total_cost()
      statement_count = self.repository.count_statements()
      completed = self.repository.count_completed_statements()
      today_transaction = self.repository.count_today_transactions()
      month_transaction = self.repository.count_month_transactions()
      ocr_success_rate = 0

      if statement_count > 0:
          ocr_success_rate = round(
              completed / statement_count * 100,
              2,
          )

      return {
          "total_users": total_users,
          "today_tokens": int(today_tokens),
          "today_cost": float(today_cost),
          "monthly_cost": float(monthly_cost),
          "total_cost": float(total_cost),
          "statement_count": statement_count,
          "ocr_success_rate": ocr_success_rate,
          "today_transaction": today_transaction,
          "month_transaction": month_transaction,
      }

  # ==========================================
  # 사용자별 토큰 사용량
  # ==========================================
  def get_user_token_usage(self):
      rows = self.repository.get_user_token_usage()
      result = []
      for row in rows:
          result.append({
              "user_id": row[0],
              "username": row[1],
              "total_tokens": int(row[2] or 0),
              "estimated_cost": float(row[3] or 0),
          })

      return result

  # ==========================================
  # 기능별 토큰 사용량
  # ==========================================
  def get_feature_token_usage(self):
      rows = self.repository.get_feature_token_usage()
      result = []
      for row in rows:
          result.append({
              "feature_type": row[0],
              "total_tokens": int(row[1] or 0),
              "estimated_cost": float(row[2] or 0),
          })

      return result

  # ==========================================
  # 일별 비용
  # ==========================================
  def get_daily_cost(self):
      rows = self.repository.get_daily_cost()
      result = []
      for row in rows:
          result.append({
              "date": row[0],
              "cost": float(row[1] or 0),
          })

      return result

  # ==========================================
  # 토큰 제한 조회
  # ==========================================
  def get_token_limit(self):
      setting = self.repository.get_token_limit()
      if setting is None:
          return {
              "daily_token_limit": 0,
              "is_active": False,
          }

      return {
          "daily_token_limit": setting.daily_token_limit,
          "is_active": setting.is_active,
      }

  # ==========================================
  # 토큰 제한 수정
  # ==========================================
  def update_token_limit(self, limit):
      setting = self.repository.update_token_limit(limit)
      return {
          "daily_token_limit": setting.daily_token_limit,
          "is_active": setting.is_active,
      }

  # ==========================================
  # 금융상품 마지막 갱신 시각
  # ==========================================
  def get_financial_product_last_update(self):
      return self.repository.get_financial_product_last_update()
    
  # ==========================================
  # 시스템 사용량
  # ==========================================
  def get_system_status(self):

      return {
          "cpu_usage": psutil.cpu_percent(interval=1),
          "ram_usage": psutil.virtual_memory().percent,
      }