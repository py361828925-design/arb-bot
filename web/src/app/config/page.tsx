"use client";

import { useEffect, useMemo } from "react";
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Button,
  message,
  Divider,
  Row,
  Col,
  Space,
  Tooltip,
} from "antd";
import useSWRImmutable from "swr/immutable";
import { InfoCircleOutlined } from "@ant-design/icons";

import { fetchConfig, updateConfig } from "@/lib/configApi";

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
  <Space>
    <span>{label}</span>
    <Tooltip title={description}>
      <InfoCircleOutlined />
    </Tooltip>
  </Space>
);

export default function ConfigPage() {
const { data, isLoading, mutate } = useSWRImmutable("/config/current", fetchConfig, {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
});

  const [form] = Form.useForm();

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

  const onFinish = async (values: any) => {
    try {
      await updateConfig(values);
      message.success("保存成功");
      mutate();
    } catch (error) {
      console.error(error);
      message.error("保存失败");
    }
  };

  const thresholdItems = useMemo(() => {
    return thresholdMeta.map((meta) => (
      <Col span={8} key={meta.key}>
        <Form.Item
          label={renderLabel(meta.label, meta.description)}
          name={["thresholds", meta.key]}
        >
          <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
        </Form.Item>
      </Col>
    ));
  }, []);

  const riskItems = useMemo(() => {
    return riskMeta.map((meta) => (
      <Col span={8} key={meta.key}>
        <Form.Item
          label={renderLabel(meta.label, meta.description)}
          name={["risk_limits", meta.key]}
        >
          <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
        </Form.Item>
      </Col>
    ));
  }, []);

  const intervalItems = useMemo(() => {
    return intervalMeta.map((meta) => (
      <Col span={8} key={meta.key}>
        <Form.Item
          label={renderLabel(meta.label, meta.description)}
          name={meta.key}
        >
          <InputNumber min={meta.min} step={meta.step} style={{ width: "100%" }} />
        </Form.Item>
      </Col>
    ));
  }, []);

  return (
    <Card
      title="策略参数配置"
      loading={isLoading}
      style={{ background: "#0b162b", color: "#e2e8f0" }}
    >
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item label="策略总开关" name="global_enable" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="停用" />
        </Form.Item>

        <Divider orientation="left">资金费率阈值</Divider>
        <Row gutter={16}>{thresholdItems}</Row>

        <Divider orientation="left">风险与费用限制</Divider>
        <Row gutter={16}>{riskItems}</Row>

        <Divider orientation="left">调度间隔</Divider>
        <Row gutter={16}>{intervalItems}</Row>

        <Space>
          <Button type="primary" htmlType="submit">
            保存
          </Button>
          <Button onClick={() => form.resetFields()}>重置</Button>
        </Space>
      </Form>
    </Card>
  );
}
