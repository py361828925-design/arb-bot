"use client";

import useSWR from "swr";
import { Card, Layout, Table, Typography, Spin } from "antd";
import dynamic from "next/dynamic";

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
    xAxis: { label: { autoHide: true, autoRotate: false } },
    yAxis: { label: { formatter: (v: string) => `${Number(v).toFixed(0)}` } },
    color: "#22c55e",
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
    xAxis: { label: { autoHide: true, autoRotate: false } },
    yAxis: { label: { formatter: (v: string) => `${Number(v).toFixed(0)}` } },
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
      </Spin>
    </Layout>
  );
}
