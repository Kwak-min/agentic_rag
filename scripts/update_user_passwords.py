#!/usr/bin/env python
"""사용자 비밀번호 해시 업데이트 스크립트"""

import bcrypt
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def update_passwords():
    """사용자 비밀번호 해시를 생성하고 DB에 업데이트"""

    # DB 연결
    conn = psycopg2.connect(
        host=os.getenv("PG_DB_HOST", "localhost"),
        port=int(os.getenv("PG_DB_PORT", "5432")),
        database=os.getenv("PG_DB_NAME", "synergy"),
        user=os.getenv("PG_DB_USER", "synergy"),
        password=os.getenv("PG_DB_PASSWORD", "synergy")
    )

    cur = conn.cursor()

    # admin/admin 해시 생성
    admin_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
    print(f"Admin hash generated: {admin_hash}")

    # user/user 해시 생성
    user_hash = bcrypt.hashpw(b'user', bcrypt.gensalt()).decode('utf-8')
    print(f"User hash generated: {user_hash}")

    try:
        # admin 비밀번호 업데이트
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (admin_hash, 'admin')
        )
        print(f"✅ Updated admin password (rows affected: {cur.rowcount})")

        # user 비밀번호 업데이트
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (user_hash, 'user')
        )
        print(f"✅ Updated user password (rows affected: {cur.rowcount})")

        conn.commit()
        print("\n✅ 모든 사용자 비밀번호가 성공적으로 업데이트되었습니다!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류 발생: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_passwords()
