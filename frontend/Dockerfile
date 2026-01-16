FROM node:20-alpine

WORKDIR /app

# 패키지 파일 복사
COPY package*.json ./

# 의존성 설치
RUN npm install

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 3000

# Vite 개발 서버 실행
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
