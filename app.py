from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from db_config import engine
from datetime import datetime
import calendar

from flask import Flask, render_template

app = Flask(__name__)



app = Flask(__name__)
@app.route('/buy', methods=['GET', 'POST'])
def buy_index():
    today = datetime.today()
    year = int(request.form.get('year', today.year))
    month = int(request.form.get('month', today.month))
    start_date = request.form.get('start_date', '').replace('/', '-')
    end_date = request.form.get('end_date', '').replace('/', '-')

    if not start_date or not end_date:
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"

    query = f"""
        SELECT 
            ISNULL(c.CustName, '(미등록 거래처)') AS CustName,
            SUM(x.PlanAmt) AS PlanAmt,
            SUM(x.ResultAmt) AS ResultAmt,
            CASE 
                WHEN SUM(x.PlanAmt) = 0 THEN 0
                ELSE ROUND(SUM(x.ResultAmt) / SUM(x.PlanAmt) * 100, 1)
            END AS Rate
        FROM (
            SELECT CustCode, SUM(ISNULL(Qty * DanGa, 0)) AS PlanAmt, 0 AS ResultAmt
            FROM dbo.ipGoPlan
            WHERE CONVERT(date, REPLACE(LTRIM(RTRIM(PlanDate)), '/', '-'), 23)
            BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY CustCode

            UNION ALL

            SELECT CustCode, 0 AS PlanAmt, SUM(ISNULL(Qty * DanGa, 0)) AS ResultAmt
            FROM dbo.ipGoBalinfo
            WHERE CONVERT(date, REPLACE(LTRIM(RTRIM(BalDate)), '/', '-'), 23)
            BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY CustCode
        ) x
        LEFT JOIN dbo.CustInfo c 
            ON RTRIM(LTRIM(x.CustCode)) = RTRIM(LTRIM(c.CustCode))
        GROUP BY c.CustName
        ORDER BY SUM(x.PlanAmt) DESC
    """

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        print("❌ SQL Error:", e)
        df = pd.DataFrame()

    if df.empty:
        return render_template("buy_index.html",
                               years=[str(y) for y in range(today.year - 3, today.year + 2)],
                               months=[str(i) for i in range(1, 13)],
                               selected_year=str(year),
                               selected_month=str(month),
                               start_date=start_date.replace('-', '/'),
                               end_date=end_date.replace('-', '/'),
                               labels=[], plan_data=[], result_data=[], cust_tables=[])

    df["Rate"] = df.apply(
        lambda r: round((r["ResultAmt"] / r["PlanAmt"]) * 100, 1)
        if r["PlanAmt"] != 0 else 0, axis=1
    )

    total_plan = int(df["PlanAmt"].sum())
    total_result = int(df["ResultAmt"].sum())
    total_rate = round((total_result / total_plan) * 100, 1) if total_plan != 0 else 0

    total_row = pd.DataFrame([{
        "CustName": "합계",
        "PlanAmt": total_plan,
        "ResultAmt": total_result,
        "Rate": total_rate
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    labels = df["CustName"].tolist()
    plan_data = df["PlanAmt"].tolist()
    result_data = df["ResultAmt"].tolist()

    return render_template("buy_index.html",
                           years=[str(y) for y in range(today.year - 3, today.year + 2)],
                           months=[str(i) for i in range(1, 13)],
                           selected_year=str(year),
                           selected_month=str(month),
                           start_date=start_date.replace('-', '/'),
                           end_date=end_date.replace('-', '/'),
                           labels=labels,
                           plan_data=plan_data,
                           result_data=result_data,
                           cust_tables=df.to_dict("records"))

@app.route('/', methods=['GET', 'POST'])
def index():
    today = datetime.today()

    # 기본값: 올해/이번달
    year = int(request.form.get('year', today.year))
    month = int(request.form.get('month', today.month))

    # "/" → "-" 변환 (SQL Server 호환)
    start_date = request.form.get('start_date', '').replace('/', '-')
    end_date = request.form.get('end_date', '').replace('/', '-')

    # 날짜가 비어있으면 이번달 자동 입력
    if not start_date or not end_date:
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"

    # ✅ 거래처명 기준 쿼리 (CustCode 공백, NULL, 타입 문제 방지)
    query = f"""
        SELECT 
            ISNULL(c.CustName, '(미등록 거래처)') AS CustName,
            SUM(x.PlanAmt) AS PlanAmt,
            SUM(x.ResultAmt) AS ResultAmt,
            CASE 
                WHEN SUM(x.PlanAmt) = 0 THEN 0
                ELSE ROUND(SUM(x.ResultAmt) / SUM(x.PlanAmt) * 100, 1)
            END AS Rate
        FROM (
            SELECT CustCode, SUM(ISNULL(Qty * DanGa, 0)) AS PlanAmt, 0 AS ResultAmt
            FROM dbo.SalePlan
            WHERE CONVERT(date, PlanDate) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY CustCode

            UNION ALL

            SELECT CustCode, 0 AS PlanAmt, SUM(ISNULL(Qty * DanGa, 0)) AS ResultAmt
            FROM dbo.SubulInfo
            WHERE CONVERT(date, ChulDate) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY CustCode
        ) x
        LEFT JOIN dbo.CustInfo c 
            ON RTRIM(LTRIM(x.CustCode)) = RTRIM(LTRIM(c.CustCode))
        GROUP BY c.CustName
        ORDER BY SUM(x.PlanAmt) DESC
    """

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        print("❌ SQL Error:", e)
        df = pd.DataFrame()

    # ✅ 데이터가 없을 경우
    if df.empty:
        return render_template(
            "index.html",
            years=[str(y) for y in range(today.year-3, today.year+2)],
            months=[str(i) for i in range(1, 13)],
            selected_year=str(year),
            selected_month=str(month),
            start_date=start_date.replace('-', '/'),
            end_date=end_date.replace('-', '/'),
            labels=[], plan_data=[], result_data=[], cust_tables=[]
        )

    # ✅ 달성률 계산
    df["Rate"] = df.apply(
        lambda r: round((r["ResultAmt"] / r["PlanAmt"]) * 100, 1)
        if r["PlanAmt"] != 0 else 0,
        axis=1
    )

    # ✅ 합계 계산
    total_plan = int(df["PlanAmt"].sum())
    total_result = int(df["ResultAmt"].sum())
    total_rate = round((total_result / total_plan) * 100, 1) if total_plan != 0 else 0

    # ✅ 합계 행 추가
    total_row = pd.DataFrame([{
        "CustName": "합계",
        "PlanAmt": total_plan,
        "ResultAmt": total_result,
        "Rate": total_rate
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    # ✅ 그래프 데이터
    labels = df["CustName"].tolist()
    plan_data = df["PlanAmt"].tolist()
    result_data = df["ResultAmt"].tolist()


    # ✅ HTML 렌더링
    return render_template(
        "index.html",
        years=[str(y) for y in range(today.year-3, today.year+2)],
        months=[str(i) for i in range(1, 13)],
        selected_year=str(year),
        selected_month=str(month),
        start_date=start_date.replace('-', '/'),
        end_date=end_date.replace('-', '/'),
        labels=labels,
        plan_data=plan_data,
        result_data=result_data,
        cust_tables=df.to_dict("records")
    )

if __name__ == "__main__":
    app.run(debug=True)
