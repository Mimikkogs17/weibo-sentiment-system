模型太大了，所以网盘分享

通过网盘分享的文件：checkpoint-669.zip
链接: https://pan.baidu.com/s/1ZNuJGdBzHJo0noTUKufxNw?pwd=nb2x 提取码: nb2x

初始化环境后，可以查看项目架构对比文件存放位置

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