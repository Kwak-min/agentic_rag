FROM node:18-alpine

WORKDIR /app

# 패키지 파일 복사
COPY package*.json ./

# 의존성 설치
RUN npm install

# 소스 코드 복사
COPY . .

# 환경 변수 설정
ENV NEXT_PUBLIC_API_URL=http://localhost:5000

# 포트 노출
EXPOSE 3000

# 개발 모드로 실행 (hot reload 지원)
CMD ["npm", "run", "dev"]
