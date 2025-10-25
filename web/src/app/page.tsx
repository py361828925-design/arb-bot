"use client";

import useSWR from "swr";
import { useCallback, useMemo, useState } from "react";
import {
  Button,
  Card,
  Col,
  Divider,
  Flex,
  Row,
  Segmented,
  Skeleton,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";

import {
  fetchDynamicStats,
  fetchOpenPositions,
  type DynamicStats,
  type OpenPosition,
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
  const [refreshMode, setRefreshMode] = useState<"auto" | "manual">("auto");
  const [valueMetric, setValueMetric] = useState<"notional" | "duration">("notional");
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const swrOptions = {
    refreshInterval: refreshMode === "auto" ? 5000 : 0,
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  };

  const {
    data: dynamicStats,
    isLoading: loadingDynamic,
    error: dynamicError,
    mutate: refetchDynamic,
  } = useSWR<DynamicStats>("/stats/dynamic", fetchDynamicStats, {
    ...swrOptions,
    onSuccess: (stats) => {
      if (stats.updated_at) {
        setLastUpdated(new Date(stats.updated_at).toLocaleString());
      }
    },
  });

  const {
    data: positions,
    isLoading: loadingPositions,
    error: positionsError,
    mutate: refetchPositions,
  } = useSWR<OpenPosition[]>("/positions/open", fetchOpenPositions, swrOptions);

  const handleRefreshModeChange = useCallback((value: string | number) => {
    setRefreshMode(value === "manual" ? "manual" : "auto");
  }, []);

  const handleMetricChange = useCallback((value: string | number) => {
    setValueMetric(value === "duration" ? "duration" : "notional");
  }, []);

  const handleRefreshClick = useCallback(async () => {
    await Promise.all([refetchDynamic(), refetchPositions()]);
  }, [refetchDynamic, refetchPositions]);

  const formatPercent = useCallback(
    (value: number, digits = 2) => `${(value * 100).toFixed(digits)}%`,
    []
  );

  const formatCountdown = useCallback((value: number) => {
    if (!Number.isFinite(value) || value < 0) return "-";
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = Math.floor(value % 60);
    return `${hours.toString().padStart(2, "0")}:${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }, []);

  const positionRows: PositionRow[] = useMemo(() => {
    if (!positions) return [];
    return positions.map((position) => ({
      key: position.group_id,
      symbol: position.symbol,
      long_exchange: (position.long?.exchange ?? "").toUpperCase(),
      short_exchange: (position.short?.exchange ?? "").toUpperCase(),
      long_return: Number(position.long?.return ?? 0),
      short_return: Number(position.short?.return ?? 0),
      total_return:
        Number(position.long?.return ?? 0) + Number(position.short?.return ?? 0),
      funding_diff: Number(position.current_funding_diff ?? 0),
      countdown_secs: Number(position.current_countdown_secs ?? -1),
      duration_secs: Number(position.duration_seconds ?? 0),
      notional_per_leg: Number(position.notional_per_leg ?? 0),
    }));
  }, [positions]);

  const columns = useMemo<ColumnsType<PositionRow>>(() => {
    const sharedColumns: ColumnsType<PositionRow> = [
      {
        title: "币种",
        dataIndex: "symbol",
        key: "symbol",
        render: (value: string) => (
          <Typography.Text strong>{value}</Typography.Text>
        ),
      },
      {
        title: "多 / 空 平台",
        dataIndex: "legs",
        key: "legs",
        render: (_value: unknown, row: PositionRow) => (
          <Typography.Text className="table-cell--muted">
            {row.long_exchange} 多 / {row.short_exchange} 空
          </Typography.Text>
        ),
      },
    ];

    const metricColumn: ColumnsType<PositionRow>[number] =
      valueMetric === "duration"
        ? {
            title: "持仓时长",
            dataIndex: "duration_secs",
            key: "duration_secs_alt",
            render: (value: number) => (
              <Typography.Text className="table-cell--muted">
                {formatCountdown(value)}
              </Typography.Text>
            ),
          }
        : {
            title: "名义价值",
            dataIndex: "notional_per_leg",
            key: "notional_per_leg",
            render: (value: number) => (
              <Typography.Text>
                {(value * 2).toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
                <span className="table-cell--muted"> USDT</span>
              </Typography.Text>
            ),
          };

    const restColumns: ColumnsType<PositionRow> = [
      {
        title: "回报率 (多腿)",
        dataIndex: "long_return",
        key: "long_return",
        render: (value: number) => (
          <Typography.Text className={value >= 0 ? "table-cell--positive" : "table-cell--negative"}>
            {formatPercent(value)}
          </Typography.Text>
        ),
      },
      {
        title: "回报率 (空腿)",
        dataIndex: "short_return",
        key: "short_return",
        render: (value: number) => (
          <Typography.Text className={value >= 0 ? "table-cell--positive" : "table-cell--negative"}>
            {formatPercent(value)}
          </Typography.Text>
        ),
      },
      {
        title: "回报率 (总)",
        dataIndex: "total_return",
        key: "total_return",
        render: (value: number) => (
          <Typography.Text className={value >= 0 ? "table-cell--positive" : "table-cell--negative"}>
            {formatPercent(value)}
          </Typography.Text>
        ),
      },
      {
        title: "资金费率差",
        dataIndex: "funding_diff",
        key: "funding_diff",
        render: (value: number) => (
          <Typography.Text className={Math.abs(value) >= 0.0005 ? "table-cell--positive" : "table-cell--muted"}>
            {formatPercent(value, 3)}
          </Typography.Text>
        ),
      },
      {
        title: "资金费结算倒计时",
        dataIndex: "countdown_secs",
        key: "countdown_secs",
        render: (value: number) => {
          if (value < 0) {
            return <Typography.Text className="table-cell--muted">-</Typography.Text>;
          }
          const minutes = value / 60;
          const tagClass =
            minutes <= 5
              ? "countdown-badge countdown-badge--danger"
              : minutes <= 30
              ? "countdown-badge countdown-badge--warning"
              : "countdown-badge";
          return <Tag className={tagClass}>{formatCountdown(value)}</Tag>;
        },
      },
      {
        title: "已持仓时间",
        dataIndex: "duration_secs",
        key: "duration_display",
        render: (value: number) => (
          <Typography.Text className="table-cell--muted">
            {formatCountdown(value)}
          </Typography.Text>
        ),
      },
    ];

    return [...sharedColumns, metricColumn, ...restColumns];
  }, [formatCountdown, formatPercent, valueMetric]);

  if (dynamicError || positionsError) {
    return (
      <Typography.Title level={3} style={{ color: "#ef4444", padding: "32px" }}>
        数据加载失败，请检查后端服务
      </Typography.Title>
    );
  }

  const isLoading = loadingDynamic || loadingPositions;
  const topStats = dynamicStats
    ? [
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
      ]
    : [];

  const logicStats = dynamicStats
    ? [
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
      ]
    : [];

  const refreshLabel = refreshMode === "auto" ? "数据每 5 秒刷新" : "手动刷新模式";

  return (
    <div className="dashboard-shell">
  <Card className="dashboard-hero" variant="borderless">
        <Flex justify="space-between" align="flex-start" gap={16} wrap="wrap">
          <div>
            <Typography.Text className="dashboard-eyebrow">策略驾驶舱</Typography.Text>
            <Typography.Title level={1} className="dashboard-hero__title">
              彭老板的印钞机
            </Typography.Title>
            <Typography.Paragraph className="dashboard-hero__subtitle">
              跨交易所资金费率套利 · 实时监控面板
            </Typography.Paragraph>
            <Space size="middle" className="dashboard-hero__actions">
              <Button type="primary" href="/history" size="large">
                历史统计
              </Button>
              <Button onClick={handleRefreshClick} size="large" ghost>
                手动刷新
              </Button>
            </Space>
          </div>
          <Card className="dashboard-meta" variant="borderless">
            <Typography.Text className="dashboard-meta__label">数据刷新</Typography.Text>
            <Segmented
              value={refreshMode}
              onChange={handleRefreshModeChange}
              options={[
                { label: "自动刷新", value: "auto" },
                { label: "手动刷新", value: "manual" },
              ]}
            />
            <Divider className="dashboard-meta__divider" />
            <Typography.Text className="dashboard-meta__label">展示指标</Typography.Text>
            <Segmented
              value={valueMetric}
              onChange={handleMetricChange}
              options={[
                { label: "名义价值", value: "notional" },
                { label: "持仓时长", value: "duration" },
              ]}
            />
            {lastUpdated && (
              <Typography.Paragraph className="dashboard-meta__timestamp">
                最近更新时间：{lastUpdated}
              </Typography.Paragraph>
            )}
          </Card>
        </Flex>
      </Card>

      <Typography.Title level={4} className="section-title">
        核心指标
      </Typography.Title>

      <Row gutter={[16, 16]}>
        {isLoading && !dynamicStats ? (
          <Col span={24}>
            <Skeleton active paragraph={{ rows: 1 }} className="skeleton-card" />
          </Col>
        ) : (
          topStats.map((card) => (
            <Col xs={24} sm={12} md={12} lg={6} key={card.title}>
              <Card className="stat-card" variant="borderless">
                <Statistic
                  title={card.title}
                  value={card.amount.toFixed(2)}
                  suffix=" USDT"
                  valueStyle={{
                    color:
                      card.title === "净利润"
                        ? card.amount >= 0
                          ? "var(--success-500)"
                          : "var(--danger-500)"
                        : "var(--text-primary)",
                  }}
                />
                {card.count !== null && (
                  <div className="stat-card__meta">数量：{card.count}</div>
                )}
              </Card>
            </Col>
          ))
        )}
      </Row>

      <Typography.Title level={4} className="section-title">
        平仓逻辑分布
      </Typography.Title>

      <Row gutter={[16, 16]} className="logic-grid">
        {isLoading && !dynamicStats ? (
          <Col span={24}>
            <Skeleton active paragraph={{ rows: 1 }} className="skeleton-card" />
          </Col>
        ) : (
          logicStats.map((card) => (
            <Col xs={12} md={8} lg={4} key={card.title}>
              <Card variant="borderless">
                <Statistic
                  title={card.title}
                  value={card.amount.toFixed(2)}
                  suffix=" USDT"
                />
                <div className="logic-grid__count">数量：{card.count}</div>
              </Card>
            </Col>
          ))
        )}
      </Row>

      <Card
        className="data-card"
        title="实时仓位"
        variant="borderless"
        extra={<span className="table-cell--muted">{refreshLabel}</span>}
      >
        {loadingPositions ? (
          <Skeleton active paragraph={{ rows: 6 }} className="skeleton-table" />
        ) : (
          <Table
            columns={columns}
            dataSource={positionRows}
            pagination={{ pageSize: 8, showSizeChanger: false }}
            rowClassName={(record: PositionRow) => {
              if (record.total_return >= 0.02) return "dark-table-row table-row-positive";
              if (record.total_return <= -0.01) return "dark-table-row table-row-negative";
              return "dark-table-row";
            }}
            locale={{
              emptyText: <div className="empty-hint">当前没有持仓，等待机会出现...</div>,
            }}
            scroll={{ x: "max-content" }}
          />
        )}
      </Card>
    </div>
  );
}
