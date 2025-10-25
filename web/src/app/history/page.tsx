"use client";

import useSWR from "swr";
import {
  Card,
  Layout,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import dynamic from "next/dynamic";
import dayjs from "dayjs";
import classNames from "classnames";

import {
  fetchSnapshotList,
  fetchRecentEvents,
  type SnapshotSummary,
  type PositionEventItem,
} from "@/lib/statsApi";

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

export default function HistoryPage() {
  const { data, isLoading, error } = useSWR<SnapshotSummary[]>(
    "/stats/static/list",
    () => fetchSnapshotList(60),
    { refreshInterval: 5000 }
  );

  const {
    data: events,
    isLoading: loadingEvents,
    error: eventsError,
  } = useSWR<PositionEventItem[]>(
    "/events/recent",
    () => fetchRecentEvents(100),
    { refreshInterval: 5000 }
  );

  const hasError = Boolean(error || eventsError);
  const dataSource = (data ?? []).map((item, idx) => ({
    key: item.snapshot_date ?? idx.toString(),
    ...item,
  }));

  const eventDataSource = (events ?? []).map((item) => ({
    ...item,
    realized_pnl: item.realized_pnl ?? null,
  }));

  const lineConfig = {
    data: dataSource,
    padding: "auto",
    xField: "snapshot_date",
    yField: "net_profit",
    smooth: true,
    height: 280,
    point: { size: 3, shape: "diamond" },
    theme: {
      styleSheet: {
        fontFamily: "Inter",
        brandColor: "#38bdf8",
        textColor: "#e2e8f0",
        backgroundColor: "transparent",
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

  const columnData = dataSource.flatMap((item) => [
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
    height: 280,
    theme: {
      styleSheet: {
        fontFamily: "Inter",
        brandColor: "#38bdf8",
        textColor: "#e2e8f0",
        backgroundColor: "transparent",
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

  if (hasError) {
    return (
      <Layout className="history-layout">
        <Typography.Title level={3} style={{ color: "#ef4444" }}>
          历史统计数据获取失败，请检查服务状态
        </Typography.Title>
      </Layout>
    );
  }

  return (
    <Layout className="history-layout">
      <Spin spinning={isLoading && !data}>
        <Space direction="vertical" size={20} style={{ width: "100%" }}>
          <div>
            <Typography.Title level={2} style={{ marginBottom: 8 }}>
              历史统计
            </Typography.Title>
            <Typography.Paragraph style={{ color: "var(--text-muted)", marginBottom: 0 }}>
              最近 60 个快照周期的盈亏、开平仓表现及决策逻辑分布
            </Typography.Paragraph>
          </div>

          <Card className="chart-card" title="净利润趋势" variant="borderless">
            <Line {...lineConfig} />
          </Card>

          <Card className="chart-card" title="各逻辑平仓金额" variant="borderless">
            <Column {...columnConfig} />
          </Card>

          <Card className="chart-card" title="每日统计快照" variant="borderless">
            <Table
              columns={tableColumns}
              dataSource={dataSource}
              pagination={false}
              rowClassName={() => "dark-table-row"}
              locale={{ emptyText: <div className="empty-hint">暂无历史统计数据</div> }}
              scroll={{ x: 900 }}
            />
          </Card>

          <Card className="chart-card" title="开/平仓事件" variant="borderless">
            <Spin spinning={loadingEvents && !events}>
              <Table
                columns={eventColumns}
                dataSource={eventDataSource}
                rowKey="id"
                pagination={{ pageSize: 20 }}
                rowClassName={() => "dark-table-row"}
                locale={{ emptyText: <div className="empty-hint">近期没有事件记录</div> }}
              />
            </Spin>
          </Card>
        </Space>
      </Spin>
    </Layout>
  );
}
