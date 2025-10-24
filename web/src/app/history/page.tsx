"use client";

import useSWR from "swr";
import { Card, Layout, Table, Typography, Spin } from "antd";
import dynamic from "next/dynamic";
import dayjs from "dayjs";
import classNames from "classnames";

import { fetchSnapshotList } from "@/lib/statsApi";

const Line = dynamic(() => import("@ant-design/plots").then((m) => m.Line), {
  ssr: false,
});
const Column = dynamic(() => import("@ant-design/plots").then((m) => m.Column), {
  ssr: false,
});

const tableColumns = [
  { title: "日期", dataIndex: "snapshot_date" },
  {
    title: "开仓总计",
    dataIndex: "total_open",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "平仓总计",
    dataIndex: "total_close",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "净利润",
    dataIndex: "net_profit",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "逻辑1金额",
    dataIndex: "logic1_amount",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "逻辑2金额",
    dataIndex: "logic2_amount",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "逻辑3金额",
    dataIndex: "logic3_amount",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "逻辑4金额",
    dataIndex: "logic4_amount",
    render: (val: number) => val.toFixed(2),
  },
  {
    title: "逻辑5金额",
    dataIndex: "logic5_amount",
    render: (val: number) => val.toFixed(2),
  },
];

export default function HistoryPage() {
  const { data, isLoading, error } = useSWR(
    "/stats/static/list",
    () => fetchSnapshotList(60),
    { refreshInterval: 5000 }
  );

const { data: events, isLoading: loadingEvents, error: eventsError } = useSWR(
  "/events/recent",
  () => fetchRecentEvents(100),
  { refreshInterval: 5000 }
);

const eventColumns = [
  {
    title: "时间",
    dataIndex: "created_at",
    render: (value: string) => dayjs(value).format("YYYY-MM-DD HH:mm:ss"),
  },
  { title: "类型", dataIndex: "event_type" },
  { title: "币种", dataIndex: "symbol" },
  { title: "逻辑", dataIndex: "logic_reason" },
  {
    title: "名义金额",
    dataIndex: ["data", "notional_per_leg"],
    render: (value: number | undefined) => (value ? (value * 2).toFixed(2) : "-"),
  },
  {
    title: "盈亏",
    dataIndex: "realized_pnl",
    render: (val: number | null) =>
      val === null ? "-" : (
        <span className={classNames({ profit: val >= 0, loss: val < 0 })}>
          {val.toFixed(2)}
        </span>
      ),
  },
];

const eventDataSource = (events ?? []).map((item: any) => ({
  ...item,
  realized_pnl: item.realized_pnl ?? null,
}));


  if (error) {
    return (
      <Layout style={{ minHeight: "100vh", padding: "32px" }}>
        <Typography.Title level={4} style={{ color: "#ef4444" }}>
          无法加载历史统计
        </Typography.Title>
      </Layout>
    );
  }

  const dataSource = (data ?? []).map((item: any, idx: number) => ({
    key: idx,
    ...item,
  }));

const lineConfig = {
  data: dataSource,
  padding: "auto",
  xField: "snapshot_date",
  yField: "net_profit",
  smooth: true,
  height: 250,
  point: { size: 3, shape: "diamond" },
  theme: {
    styleSheet: {
      fontFamily: "Inter",
      brandColor: "#38bdf8",
      textColor: "#e2e8f0",
      backgroundColor: "#0b162b",
    },
  },
  legend: {
    itemName: { style: { fill: "#e2e8f0" } },
  },
  xAxis: {
    label: { style: { fill: "#e2e8f0" } },
    line: { style: { stroke: "#334155" } },
    grid: { line: { style: { stroke: "#1e293b" } } },
  },
  yAxis: {
    label: { style: { fill: "#e2e8f0" } },
    grid: { line: { style: { stroke: "#1e293b" } } },
  },
  tooltip: {
    domStyles: {
      "g2-tooltip": {
        backgroundColor: "#1e293b",
        color: "#e2e8f0",
        border: "1px solid #334155",
      },
    },
  },
};


  const columnData = dataSource.flatMap((item: any) => [
    { snapshot_date: item.snapshot_date, logic: "逻辑1", value: item.logic1_amount },
    { snapshot_date: item.snapshot_date, logic: "逻辑2", value: item.logic2_amount },
    { snapshot_date: item.snapshot_date, logic: "逻辑3", value: item.logic3_amount },
    { snapshot_date: item.snapshot_date, logic: "逻辑4", value: item.logic4_amount },
    { snapshot_date: item.snapshot_date, logic: "逻辑5", value: item.logic5_amount },
  ]);

const columnConfig = {
  data: columnData,
  xField: "snapshot_date",
  yField: "value",
  seriesField: "logic",
  isGroup: true,
  height: 250,
  theme: {
    styleSheet: {
      fontFamily: "Inter",
      brandColor: "#38bdf8",
      textColor: "#e2e8f0",
      backgroundColor: "#0b162b",
    },
  },
  legend: {
    itemName: { style: { fill: "#e2e8f0" } },
  },
  xAxis: {
    label: { style: { fill: "#e2e8f0" } },
    line: { style: { stroke: "#334155" } },
  },
  yAxis: {
    label: { style: { fill: "#e2e8f0" } },
    grid: { line: { style: { stroke: "#1e293b" } } },
  },
  tooltip: {
    domStyles: {
      "g2-tooltip": {
        backgroundColor: "#1e293b",
        color: "#e2e8f0",
        border: "1px solid #334155",
      },
    },
  },
};

  return (
    <Layout style={{ minHeight: "100vh", padding: "32px" }}>
      <Spin spinning={isLoading}>
        <Typography.Title level={3} style={{ color: "#22c55e" }}>
          历史统计
        </Typography.Title>

        <Card title="净利润趋势" style={{ marginTop: 16, background: "#0b162b" }}>
          <Line {...lineConfig} />
        </Card>

        <Card title="各逻辑平仓金额" style={{ marginTop: 16, background: "#0b162b" }}>
          <Column {...columnConfig} />
        </Card>

        <Card title="每日统计快照" style={{ marginTop: 16, background: "#0b162b" }}>
          <Table columns={tableColumns} dataSource={dataSource} pagination={false} />
        </Card>

        <Card
          title="开/平仓事件"
          style={{ marginTop: 16, background: "#0b162b" }}
          styles={{ body: { padding: 0 } }}
        >
          <Spin spinning={loadingEvents}>
            <Table
              columns={eventColumns}
              dataSource={eventDataSource}
              rowKey="id"
              pagination={{ pageSize: 20 }}
            />
          </Spin>
        </Card>
      </Spin>
    </Layout>
  );
}
