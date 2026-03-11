启动步骤
数据库：
mysql -uroot -p < backend/app/sql/init.sql
后端：
cd backend
python -m venv .venv
 .venv\Scripts\activate
python run.py
前端：
cd frontend
npm install
npm run dev
爬虫：
streamlit run web/main.py
