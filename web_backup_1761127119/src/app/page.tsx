"use client";

import { useMemo } from "react";
import useSWR from "swr";
import {
  Card,
  Col,
  Row,
  Statistic,
  Table,
  Tag,
  Layout,
  Typography,
  Space,
  Button,
  Spin,
} from "antd";
import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import classNames from "classnames";

import {
  fetchDynamicStats,
  fetchOpenPositions,
} from "@/lib/statsApi";

dayjs.extend(duration);

type PositionRow = {
  key: string;
  symbol: string;
  margin: number;
  leverage: number;
  notional: number;
  longExchange: string;
  shortExchange: string;
  longReturn: number;
  shortReturn: number;
  totalReturn: number;
  fundingDiff: number;
  countdownSecs: number;
  durationSecs: number;
};

const countdownText = (secs: number) => {
  if (secs < 0) return "-";
  const d = dayjs.duration(secs, "seconds");
  return `${String(d.hours()).padStart(2, "0")}:${String(
    d.minutes()
  ).padStart(2, "0")}:${String(d.seconds()).padStart(2, "0")}`;
};

export default function DashboardPage() {
  const {
    data: dynamicStats,
    isLoading: loadingDynamic,
    error: dynamicError,
  } = useSWR("/stats/dynamic", fetchDynamicStats, { refreshInterval: 5000 });

  const {
    data: positions,
    isLoading: loadingPositions,
    error: positionsError,
  } = useSWR("/positions/open", fetchOpenPositions, { refreshInterval: 5000 });

  const columns = useMemo(
    () => [
      { title: "币种", dataIndex: "symbol" },
      {
        title: "开仓本金",
        dataIndex: "margin",
        render: (val: number) => `${val.toLocaleString()} USDT`,
      },
      { title: "杠杆", dataIndex: "leverage" },
      {
        title: "仓位价值",
        dataIndex: "notional",
        render: (val: number) => `${val.toLocaleString()} USDT`,
      },
      {
        title: "币安 / Bitget",
        dataIndex: "legs",
        render: (_: any, record: PositionRow) => (
          <Space size={4}>
            <Tag color="success">{record.longExchange} 多</Tag>
            <Tag color="error">{record.shortExchange} 空</Tag>
          </Space>
        ),
      },
      {
        title: "回报率%",
        dataIndex: "totalReturn",
          render: (val: number) => (
          <span className={classNames({ profit: val >= 0, loss: val < 0 })}>
            {(val * 100).toFixed(2)}%
          </span>
        ),
      },
      {
        title: "资金费率%",
        dataIndex: "fundingDiff",
        render: (val: number) => `${(val * 100).toFixed(3)}%`,
      },
      {
        title: "资金费结算倒计时",
        dataIndex: "countdownSecs",
        render: countdownText,
      },
      {
        title: "仓位持续时间",
        dataIndex: "durationSecs",
        render: countdownText,
      },
    ],
    []
  );

  const positionRows: PositionRow[] = (positions ?? []).map(
    (grp: any) => ({
      key: grp.group_id,
      symbol: grp.symbol,
      margin: grp.margin_per_leg ?? 0,
      leverage: grp.leverage ?? 0,
      notional: grp.notional_per_leg ?? 0,
      longExchange: grp.long_exchange,
      shortExchange: grp.short_exchange,
      longReturn: grp.long_return ?? 0,
      shortReturn: grp.short_return ?? 0,
      totalReturn: grp.total_return ?? 0,
      fundingDiff: grp.current_funding_diff ?? 0,
      countdownSecs: grp.current_countdown_secs ?? -1,
      durationSecs: grp.duration_seconds ?? 0,
    })
  );

  if (dynamicError || positionsError) {
    return (
      <Layout style={{ minHeight: "100vh", padding: "32px" }}>
        <Typography.Title level={4} style={{ color: "#ef4444" }}>
          无法加载实时统计，请检查后端服务
        </Typography.Title>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Layout.Header style={{ background: "transparent", padding: "16px 32px" }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Typography.Title level={3} style={{ margin: 0, color: "#22c55e" }}>
              跨交易所资金费率套利控制台
            </Typography.Title>
            <Typography.Text type="secondary">
              环境：Production | 模式：Simulation
            </Typography.Text>
          </Col>
          <Col>
            <Space>
              <Button type="primary">全局开关</Button>
              <Button danger>紧急停止</Button>
            </Space>
          </Col>
        </Row>
      </Layout.Header>

      <Layout.Content style={{ padding: "0 32px 32px" }}>
        <Spin spinning={loadingDynamic || loadingPositions}>
          {dynamicStats && (
            <>
              <Row gutter={[16, 16]}>
                {[
                  { title: "实时仓位", value: dynamicStats.active_notional },
                  { title: "开仓总计", value: dynamicStats.total_open },
                  { title: "平仓总计", value: dynamicStats.total_close },
                  { title: "净利润", value: dynamicStats.net_profit },
                ].map((card) => (
                  <Col span={6} key={card.title}>
                    <Card variant="borderless" style={{ background: "#111c33" }}>
                      <Statistic
                        title={card.title}
                        value={card.value.toFixed(2)}
                        suffix=" USDT"
                        valueStyle={{
                          color:
                            card.title === "净利润"
                              ? card.value >= 0
                                ? "#22c55e"
                                : "#ef4444"
                              : "#e2e8f0",
                        }}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>

              <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                {[
                  { title: "1逻辑平仓", value: dynamicStats.logic1_amount },
                  { title: "2逻辑平仓", value: dynamicStats.logic2_amount },
                  { title: "3逻辑平仓", value: dynamicStats.logic3_amount },
                  { title: "4逻辑平仓", value: dynamicStats.logic4_amount },
                  { title: "5逻辑平仓", value: dynamicStats.logic5_amount },
                ].map((item) => (
                  <Col span={4} key={item.title}>
                    <Card size="small" style={{ background: "#091227" }}>
                      <Statistic
                        title={item.title}
                        value={item.value.toFixed(2)}
                        suffix=" USDT"
                        valueStyle={{ color: "#94a3b8", fontSize: 18 }}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            </>
          )}

          <Card
            title="实时仓位"
            style={{ marginTop: 24, background: "#0b162b" }}
            bodyStyle={{ padding: 0 }}
          >
            <Table
              dataSource={positionRows}
              columns={columns}
              pagination={false}
              rowClassName={(record: PositionRow) =>
                record.totalReturn >= 0 ? "profit" : "loss"
              }
            />
          </Card>
        </Spin>
      </Layout.Content>
    </Layout>
  );
}
