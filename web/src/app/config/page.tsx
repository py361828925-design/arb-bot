"use client";

import { useCallback, useEffect, useMemo } from "react";
import dayjs from "dayjs";
import {
  Button,
  Card,
  Col,
  Divider,
  Flex,
  Form,
  InputNumber,
  Row,
  Skeleton,
  Space,
  Switch,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import useSWRImmutable from "swr/immutable";

import { fetchConfig, updateConfig } from "@/lib/configApi";
import { type ConfigFormValues } from "@/types/config";

const thresholdMeta = [
  {
    key: "aa",
    label: "阈值 aa",
    description: "资金费率差 |diff| ≥ aa 时才考虑开仓",
    min: 0,
    step: 0.0001,
  },
  {
    key: "bb",
    label: "阈值 bb",
    description: "资金费率差回落到 ≤ bb 时触发逻辑1 平仓",
    min: 0,
    step: 0.0001,
  },
  {
    key: "cc",
    label: "阈值 cc",
    description: "当总回报 ≥ cc 且差值回落时平仓",
    min: 0,
    step: 0.0001,
  },
  {
    key: "dd",
    label: "阈值 dd (分钟)",
    description: "距资金费结算 ≤ dd 分钟时触发逻辑1",
    min: 0,
    step: 1,
  },
  {
    key: "ee",
    label: "阈值 ee",
    description: "单腿亏损达到 hh 但总回报 ≥ ee 时平仓（逻辑2）",
    min: 0,
    step: 0.0001,
  },
  {
    key: "ff",
    label: "阈值 ff",
    description: "总回报 ≥ ff 时立即平仓（逻辑3）",
    min: 0,
    step: 0.0001,
  },
  {
    key: "gg",
    label: "阈值 gg",
    description: "逻辑4：当组合回报率 ≤ -gg% 时止损平仓",
    min: 0,
    step: 0.0001,
  },
  {
    key: "hh",
    label: "阈值 hh",
    description: "逻辑2：单腿亏损达到 hh% 时触发",
    min: 0,
    step: 0.1,
  },
];

const riskMeta = [
  {
    key: "group_max",
    label: "最大仓位组数 group_max",
    description: "最多允许同时存在的仓位组数量",
    min: 0,
    step: 1,
  },
  {
    key: "duplicate_max",
    label: "同币重复开仓 duplicate_max",
    description: "同一币种最多允许存在的仓位组数量",
    min: 0,
    step: 1,
  },
  {
    key: "leverage_max",
    label: "最大杠杆 leverage_max",
    description: "开仓默认不超过此杠杆倍数",
    min: 0,
    step: 0.1,
  },
  {
    key: "margin_per_leg",
    label: "单腿保证金 margin_per_leg",
    description: "每一条腿的保证金设置",
    min: 0,
    step: 1,
  },
  {
    key: "taker_fee",
    label: "吃单费率 taker_fee",
    description: "策略计算时所用的吃单手续费",
    min: 0,
    step: 0.0001,
  },
  {
    key: "maker_fee",
    label: "挂单费率 maker_fee",
    description: "策略计算时所用的挂单手续费",
    min: 0,
    step: 0.0001,
  },
  {
    key: "trade_fee",
    label: "交易费 trade_fee",
    description: "整体手续费假设（可与 taker/maker 统一）",
    min: 0,
    step: 0.0001,
  },
];

const intervalMeta = [
  {
    key: "scan_interval_seconds",
    label: "扫描间隔 (秒)",
    description: "资金费率 / 行情扫描频率",
    min: 0,
    step: 0.5,
  },
  {
    key: "close_interval_seconds",
    label: "平仓检查间隔 (秒)",
    description: "风控轮询平仓逻辑的频率",
    min: 0,
    step: 0.5,
  },
  {
    key: "open_interval_seconds",
    label: "开仓检查间隔 (秒)",
    description: "策略刷新开仓机会的频率",
    min: 0,
    step: 0.5,
  },
];

const renderLabel = (label: string, description: string) => (
  <Space size={6} align="center">
    <span>{label}</span>
    <Tooltip title={description}>
      <span className="label-hint">?</span>
    </Tooltip>
  </Space>
);

export default function ConfigPage() {
  const { data, isLoading, mutate } = useSWRImmutable(
    "/config/current",
    fetchConfig,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  const [form] = Form.useForm<ConfigFormValues>();

  useEffect(() => {
    if (data) {
      form.setFieldsValue({
        global_enable: data.global_enable,
        thresholds: data.thresholds,
        risk_limits: data.risk_limits,
        scan_interval_seconds: data.scan_interval_seconds,
        close_interval_seconds: data.close_interval_seconds,
        open_interval_seconds: data.open_interval_seconds,
      });
    }
  }, [data, form]);

  const onFinish = async (values: ConfigFormValues) => {
    try {
      await updateConfig(values);
      message.success("保存成功");
      mutate();
    } catch (error) {
      console.error(error);
      message.error("保存失败");
    }
  };

  const handleRefresh = useCallback(async () => {
    const hide = message.loading("正在同步最新配置…", 0);
    try {
      await mutate();
      message.success("已获取最新配置");
    } catch (error) {
      console.error(error);
      message.error("刷新失败，请稍后重试");
    } finally {
      hide();
    }
  }, [mutate]);

  const handleReset = useCallback(() => {
    form.resetFields();
  }, [form]);

  const thresholdItems = useMemo(
    () =>
      thresholdMeta.map((meta) => (
        <Col xs={24} md={12} lg={8} key={meta.key}>
          <Form.Item
            label={renderLabel(meta.label, meta.description)}
            name={["thresholds", meta.key]}
          >
            <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
          </Form.Item>
        </Col>
      )),
    []
  );

  const riskItems = useMemo(
    () =>
      riskMeta.map((meta) => (
        <Col xs={24} md={12} lg={8} key={meta.key}>
          <Form.Item
            label={renderLabel(meta.label, meta.description)}
            name={["risk_limits", meta.key]}
          >
            <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
          </Form.Item>
        </Col>
      )),
    []
  );

  const intervalItems = useMemo(
    () =>
      intervalMeta.map((meta) => (
        <Col xs={24} md={12} lg={8} key={meta.key}>
          <Form.Item
            label={renderLabel(meta.label, meta.description)}
            name={meta.key}
          >
            <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
          </Form.Item>
        </Col>
      )),
    []
  );

  const lastUpdated = data?.created_at
    ? dayjs(data.created_at).format("YYYY-MM-DD HH:mm:ss")
    : "-";
  const loading = isLoading && !data;
  const enabled = data?.global_enable ?? false;
  const statusTag = enabled ? (
    <Tag className="config-status config-status--active">运行中</Tag>
  ) : (
    <Tag className="config-status config-status--paused">已停用</Tag>
  );

  return (
    <div className="dashboard-shell config-shell">
      <Card className="dashboard-hero" bordered={false}>
        <Flex justify="space-between" align="stretch" gap={16} wrap="wrap">
          <div>
            <Typography.Text className="dashboard-eyebrow">参数控制台</Typography.Text>
            <Typography.Title level={1} className="dashboard-hero__title">
              策略参数配置
            </Typography.Title>
            <Typography.Paragraph className="dashboard-hero__subtitle">
              调整资金费阈值与风险限制，实时下发到后端服务
            </Typography.Paragraph>
            <Space size="middle" className="dashboard-hero__actions">
              <Button type="primary" onClick={handleRefresh} size="large">
                拉取最新配置
              </Button>
              <Button onClick={handleReset} size="large" ghost>
                重置表单
              </Button>
            </Space>
          </div>
          <Card className="config-hero-card" bordered={false}>
            <Skeleton active loading={loading} paragraph={{ rows: 2 }}>
              <Typography.Text className="config-hero-card__label">
                当前状态
              </Typography.Text>
              {statusTag}
              <Divider className="config-hero-card__divider" />
              <Typography.Text className="config-hero-card__label">
                最近更新
              </Typography.Text>
              <Typography.Title level={4} className="config-hero-card__timestamp">
                {lastUpdated}
              </Typography.Title>
            </Skeleton>
          </Card>
        </Flex>
      </Card>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={loading}
        className="config-form"
      >
        <Space direction="vertical" size={24} style={{ width: "100%" }}>
          <Card className="config-card" bordered={false}>
            <Skeleton active loading={loading} paragraph={{ rows: 0 }}>
              <Flex justify="space-between" align="center" wrap="wrap" gap={16}>
                <Typography.Title level={4} className="config-card__title">
                  策略开关
                </Typography.Title>
                <Typography.Text className="table-cell--muted">
                  切换后会立即影响所有策略实例
                </Typography.Text>
              </Flex>
              <Form.Item
                label="策略总开关"
                name="global_enable"
                valuePropName="checked"
                className="config-form-item"
              >
                <Switch checkedChildren="启用" unCheckedChildren="停用" />
              </Form.Item>
            </Skeleton>
          </Card>

          <Card className="config-card" bordered={false}>
            <Skeleton active loading={loading} paragraph={{ rows: 2 }}>
              <Typography.Title level={4} className="config-card__title">
                资金费率阈值
              </Typography.Title>
              <Typography.Paragraph className="config-card__subtitle">
                控制开仓与不同平仓逻辑触发条件，单位为收益或时间阈值
              </Typography.Paragraph>
              <Row gutter={[16, 16]}>{thresholdItems}</Row>
            </Skeleton>
          </Card>

          <Card className="config-card" bordered={false}>
            <Skeleton active loading={loading} paragraph={{ rows: 2 }}>
              <Typography.Title level={4} className="config-card__title">
                风险与费用限制
              </Typography.Title>
              <Typography.Paragraph className="config-card__subtitle">
                限定整体敞口、手续费假设与每腿保证金，确保策略在安全区间运行
              </Typography.Paragraph>
              <Row gutter={[16, 16]}>{riskItems}</Row>
            </Skeleton>
          </Card>

          <Card className="config-card" bordered={false}>
            <Skeleton active loading={loading} paragraph={{ rows: 2 }}>
              <Typography.Title level={4} className="config-card__title">
                调度间隔
              </Typography.Title>
              <Typography.Paragraph className="config-card__subtitle">
                控制各服务轮询频率，合理设置可避免资源浪费或过度延迟
              </Typography.Paragraph>
              <Row gutter={[16, 16]}>{intervalItems}</Row>
            </Skeleton>
          </Card>

          <Flex justify="flex-end" align="center" gap={12} className="config-actions">
            <Button size="large" onClick={handleReset} ghost>
              重置
            </Button>
            <Button type="primary" htmlType="submit" size="large">
              保存
            </Button>
          </Flex>
        </Space>
      </Form>
    </div>
  );
}
