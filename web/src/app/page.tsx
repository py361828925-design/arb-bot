"use client";

import useSWR from "swr";
import { useMemo } from "react";
import Link from "next/link";
import {
  Card,
  Col,
  Row,
  Statistic,
  Table,
  Spin,
  Typography,
} from "antd";

import {
  fetchDynamicStats,
  fetchOpenPositions,
} from "@/lib/statsApi";

type PositionRow = {
  key: string;
  symbol: string;
  long_exchange: string;
  short_exchange: string;
  long_return: number;
  short_return: number;
  total_return: number;
  funding_diff: number;
  countdown_secs: number;
  duration_secs: number;
  notional_per_leg: number;
};

export default function DashboardPage() {

  const swrOptions = {
    refreshInterval: 5000,
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  };

  const {
    data: dynamicStats,
    isLoading: loadingDynamic,
    error: dynamicError,
  } = useSWR("/stats/dynamic", fetchDynamicStats, swrOptions);

  const {
    data: positions,
    isLoading: loadingPositions,
    error: positionsError,
  } = useSWR("/positions/open", fetchOpenPositions, swrOptions);

  const positionRows: PositionRow[] = useMemo(() => {
    if (!positions) return [];
    return positions.map((p: any) => ({
      key: p.group_id,
      symbol: p.symbol,
      long_exchange: (p.long?.exchange ?? "").toUpperCase(),
      short_exchange: (p.short?.exchange ?? "").toUpperCase(),
      long_return: Number(p.long?.return ?? 0),
      short_return: Number(p.short?.return ?? 0),
      total_return: Number(p.long?.return ?? 0) + Number(p.short?.return ?? 0),
      funding_diff: Number(p.current_funding_diff ?? 0),
      countdown_secs: Number(p.current_countdown_secs ?? -1),
      duration_secs: Number(p.duration_seconds ?? 0),
      notional_per_leg: Number(p.notional_per_leg ?? 0),
    }));
  }, [positions]);

  const columns = useMemo(
    () => [
      {
        title: "币种",
        dataIndex: "symbol",
        key: "symbol",
      },
      {
        title: "币安 / Bitget",
        dataIndex: "legs",
        key: "legs",
        render: (_: any, row: PositionRow) => (
          <span>
            {row.long_exchange} 多 / {row.short_exchange} 空
          </span>
        ),
      },
      {
        title: "名义价值",
        dataIndex: "notional_per_leg",
        key: "notional_per_leg",
        render: (value: number) => `${(value * 2).toLocaleString()} USDT`,
      },
      {
        title: "回报率 (多腿)",
        dataIndex: "long_return",
        key: "long_return",
        render: (value: number) => `${(value * 100).toFixed(2)}%`,
      },
      {
        title: "回报率 (空腿)",
        dataIndex: "short_return",
        key: "short_return",
        render: (value: number) => `${(value * 100).toFixed(2)}%`,
      },
      {
        title: "回报率 (总)",
        dataIndex: "total_return",
        key: "total_return",
        render: (value: number) => `${(value * 100).toFixed(2)}%`,
      },
      {
        title: "资金费率差",
        dataIndex: "funding_diff",
        key: "funding_diff",
        render: (value: number) => `${(value * 100).toFixed(3)}%`,
      },
      {
        title: "资金费结算倒计时",
        dataIndex: "countdown_secs",
        key: "countdown_secs",
        render: (value: number) => {
          if (value < 0) return "-";
          const hours = Math.floor(value / 3600);
          const minutes = Math.floor((value % 3600) / 60);
          const seconds = value % 60;
          return `${hours.toString().padStart(2, "0")}:${minutes
            .toString()
            .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        },
      },
      {
        title: "仓位持续时间",
        dataIndex: "duration_secs",
        key: "duration_secs",
        render: (value: number) => {
          const hours = Math.floor(value / 3600);
          const minutes = Math.floor((value % 3600) / 60);
          const seconds = value % 60;
          return `${hours.toString().padStart(2, "0")}:${minutes
            .toString()
            .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        },
      },
    ],
    []
  );

  if (dynamicError || positionsError) {
    return (
      <Typography.Title level={3} style={{ color: "#ef4444", padding: "32px" }}>
        数据加载失败，请检查后端服务
      </Typography.Title>
    );
  }

  if (loadingDynamic || loadingPositions || !dynamicStats) {
    return (
      <Spin spinning tip="加载中...">
        <div
          style={{
            height: "100vh",
            background: "#0f172a",
          }}
        />
      </Spin>
    );
  }



  const topStats = [
    {
      title: "实时仓位",
      amount: dynamicStats.active_notional,
      count: dynamicStats.active_group_count,
    },
    {
      title: "开仓总计",
      amount: dynamicStats.total_open,
      count: dynamicStats.total_open_count,
    },
    {
      title: "平仓总计",
      amount: dynamicStats.total_close,
      count: dynamicStats.total_close_count,
    },
    {
      title: "净利润",
      amount: dynamicStats.net_profit,
      count: null,
    },
  ];

  const logicStats = [
    {
      title: "1逻辑平仓",
      amount: dynamicStats.logic1_amount,
      count: dynamicStats.logic1_count,
    },
    {
      title: "2逻辑平仓",
      amount: dynamicStats.logic2_amount,
      count: dynamicStats.logic2_count,
    },
    {
      title: "3逻辑平仓",
      amount: dynamicStats.logic3_amount,
      count: dynamicStats.logic3_count,
    },
    {
      title: "4逻辑平仓",
      amount: dynamicStats.logic4_amount,
      count: dynamicStats.logic4_count,
    },
    {
      title: "5逻辑平仓",
      amount: dynamicStats.logic5_amount,
      count: dynamicStats.logic5_count,
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ position: "relative", marginBottom: 16 }}>
        <Typography.Title
          level={2}
          style={{ color: "#f8fafc", textAlign: "center", margin: 0 }}
        >
          彭老板的印钞机
        </Typography.Title>


        <Link
          href="/history"
          style={{
            background: "#1d4ed8",
            color: "#f8fafc",
            padding: "6px 12px",
            borderRadius: 6,
            textDecoration: "none",
          }}
        >
        历史统计
      </Link>
    </div>

    {/* 原来的内容继续写在后面 */}

      <Typography.Title level={3} style={{ color: "#f8fafc" }}>
        实时控制台
      </Typography.Title>

      <Row gutter={[16, 16]}>
        {topStats.map((card) => (
          <Col span={6} key={card.title}>
            <Card
              className="stat-card"
              variant="borderless"
              style={{ background: "#111c33" }}
            >
              <Statistic
                title={card.title}
                value={card.amount.toFixed(2)}
                suffix=" USDT"
                titleStyle={{ color: "#f8fafc" }}
                valueStyle={{
                  color:
                    card.title === "净利润"
                      ? card.amount >= 0
                        ? "#22c55e"
                        : "#ef4444"
                      : "#f8fafc",
                }}
              />
              {card.count !== null && (
                <div style={{ marginTop: 8, color: "#94a3b8" }}>
                  数量：{card.count}
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {logicStats.map((card) => (
          <Col span={4} key={card.title}>
            <Card
              className="stat-card"
              variant="borderless"
              style={{ background: "#111c33" }}
            >
              <Statistic
                title={card.title}
                value={card.amount.toFixed(2)}
                suffix=" USDT"
                titleStyle={{ color: "#f8fafc" }}
                valueStyle={{ color: "#f8fafc", fontSize: 18 }}
              />
              <div style={{ marginTop: 8, color: "#94a3b8" }}>
                数量：{card.count}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        className="stat-card"
        title="实时仓位"
        variant="borderless"
        style={{ marginTop: 24, background: "#0b162b" }}
      >
        <Table
          columns={columns}
          dataSource={positionRows}
          pagination={false}
          rowClassName={() => "dark-table-row"}
        />
      </Card>
    </div>
  );
}
