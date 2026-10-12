import React, { useLayoutEffect, useRef, useState } from 'react';

const HEIGHT = 240;
const MARGIN = { top: 20, right: 16, bottom: 28, left: 44 };
const LINE_COLOR = '#4f46e5'; // primary-600
const BAR_COLOR = '#a5b4fc'; // past months
const BAR_CURRENT_COLOR = '#4f46e5'; // current month
const GRID_COLOR = '#e2e8f0'; // neutral-200
const AXIS_TEXT = '#64748b'; // neutral-500

const formatNumber = (value) => value.toLocaleString('vi-VN');

const formatDay = (iso) => {
  const [, month, day] = iso.split('-');
  return `${day}/${month}`;
};

// Rounds the axis maximum up to 1/2/5 × 10^n so tick labels stay readable.
const niceTicks = (maxValue, count = 4) => {
  if (maxValue <= 0) return [0, 15, 30, 45, 60];
  const raw = maxValue / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * magnitude).find((s) => s >= raw);
  const ticks = [];
  for (let value = 0; value <= maxValue + step * 0.999; value += step) ticks.push(value);
  return ticks;
};

const useWidth = () => {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    if (!ref.current) return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
};

const Tooltip = ({ x, width, children }) => {
  const tooltipWidth = 168;
  const left = Math.min(Math.max(x - tooltipWidth / 2, 0), Math.max(width - tooltipWidth, 0));
  return (
    <div
      className="pointer-events-none absolute top-0 z-10 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm shadow-card"
      style={{ left, width: tooltipWidth }}
    >
      {children}
    </div>
  );
};

const YAxis = ({ ticks, y, plotWidth }) => (
  <g>
    {ticks.map((tick) => (
      <g key={tick}>
        <line x1={MARGIN.left} x2={MARGIN.left + plotWidth} y1={y(tick)} y2={y(tick)} stroke={GRID_COLOR} strokeWidth={1} />
        <text x={MARGIN.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" fontSize={12} fill={AXIS_TEXT}>
          {formatNumber(tick)}
        </text>
      </g>
    ))}
  </g>
);

export const DailyLateChart = ({ data }) => {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const plotWidth = Math.max(width - MARGIN.left - MARGIN.right, 0);
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const ticks = niceTicks(Math.max(0, ...data.map((d) => d.minutes)));
  const yMax = ticks[ticks.length - 1];
  const step = data.length > 1 ? plotWidth / (data.length - 1) : 0;
  const x = (i) => MARGIN.left + i * step;
  const y = (value) => MARGIN.top + plotHeight - (value / yMax) * plotHeight;
  const path = data.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d.minutes)}`).join(' ');
  const area = data.length
    ? `${path} L${x(data.length - 1)},${y(0)} L${x(0)},${y(0)} Z`
    : '';
  const labelEvery = Math.max(1, Math.ceil(data.length / Math.max(plotWidth / 56, 1)));
  const last = data.length - 1;
  const active = hover ?? null;

  const handleMove = (event) => {
    if (!data.length || !step) return;
    const box = event.currentTarget.getBoundingClientRect();
    const index = Math.round((event.clientX - box.left - MARGIN.left) / step);
    setHover(Math.min(Math.max(index, 0), last));
  };

  return (
    <div ref={ref} className="relative w-full">
      {width > 0 && (
        <svg
          width={width}
          height={HEIGHT}
          role="img"
          aria-label="Biểu đồ đường tổng số phút đi trễ theo ngày"
          onMouseMove={handleMove}
          onMouseLeave={() => setHover(null)}
        >
          <YAxis ticks={ticks} y={y} plotWidth={plotWidth} />
          {data.map((d, i) => (i % labelEvery === 0 || i === last) && (i === last || last - i >= labelEvery / 2) ? (
            <text key={d.date} x={x(i)} y={HEIGHT - 8} textAnchor="middle" fontSize={12} fill={AXIS_TEXT}>
              {formatDay(d.date)}
            </text>
          ) : null)}
          <path d={area} fill={LINE_COLOR} fillOpacity={0.08} />
          <path d={path} fill="none" stroke={LINE_COLOR} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
          {data.length > 0 && active === null && (
            <g>
              <circle cx={x(last)} cy={y(data[last].minutes)} r={4} fill={LINE_COLOR} stroke="#fff" strokeWidth={2} />
              <text x={x(last)} y={y(data[last].minutes) - 10} textAnchor="end" fontSize={12} fontWeight={600} fill="#334155">
                {formatNumber(data[last].minutes)} phút
              </text>
            </g>
          )}
          {active !== null && (
            <g>
              <line x1={x(active)} x2={x(active)} y1={MARGIN.top} y2={MARGIN.top + plotHeight} stroke="#cbd5e1" strokeWidth={1} />
              <circle cx={x(active)} cy={y(data[active].minutes)} r={5} fill={LINE_COLOR} stroke="#fff" strokeWidth={2} />
            </g>
          )}
        </svg>
      )}
      {active !== null && (
        <Tooltip x={x(active)} width={width}>
          <div className="font-semibold text-neutral-900">{formatDay(data[active].date)}</div>
          <div className="text-neutral-700">{formatNumber(data[active].minutes)} phút đi trễ</div>
          <div className="text-neutral-500">{data[active].count} lượt đi trễ</div>
        </Tooltip>
      )}
    </div>
  );
};

const barPath = (x, y, width, height, radius) => {
  if (height <= 0) return '';
  const r = Math.min(radius, width / 2, height);
  return `M${x},${y + height} V${y + r} Q${x},${y} ${x + r},${y} H${x + width - r} Q${x + width},${y} ${x + width},${y + r} V${y + height} Z`;
};

export const MonthlyLateChart = ({ data }) => {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const plotWidth = Math.max(width - MARGIN.left - MARGIN.right, 0);
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const ticks = niceTicks(Math.max(0, ...data.map((d) => d.minutes)));
  const yMax = ticks[ticks.length - 1];
  const band = data.length ? plotWidth / data.length : 0;
  const barWidth = Math.min(48, band * 0.55);
  const y = (value) => MARGIN.top + plotHeight - (value / yMax) * plotHeight;
  const center = (i) => MARGIN.left + band * i + band / 2;
  const last = data.length - 1;

  return (
    <div ref={ref} className="relative w-full">
      {width > 0 && (
        <svg width={width} height={HEIGHT} role="img" aria-label="Biểu đồ cột tổng số phút đi trễ theo tháng">
          <YAxis ticks={ticks} y={y} plotWidth={plotWidth} />
          {data.map((d, i) => {
            const top = y(d.minutes);
            const isCurrent = i === last;
            return (
              <g key={`${d.year}-${d.month}`}>
                <path
                  d={barPath(center(i) - barWidth / 2, top, barWidth, y(0) - top, 4)}
                  fill={isCurrent ? BAR_CURRENT_COLOR : BAR_COLOR}
                  opacity={hover === null || hover === i ? 1 : 0.55}
                />
                {isCurrent && (
                  <text x={center(i)} y={top - 8} textAnchor="middle" fontSize={12} fontWeight={600} fill="#334155">
                    {formatNumber(d.minutes)}
                  </text>
                )}
                <text x={center(i)} y={HEIGHT - 8} textAnchor="middle" fontSize={12} fill={isCurrent ? '#334155' : AXIS_TEXT} fontWeight={isCurrent ? 600 : 400}>
                  {`T${d.month}/${String(d.year).slice(2)}`}
                </text>
                {/* Hit target spans the whole band so thin bars are easy to hover. */}
                <rect
                  x={MARGIN.left + band * i}
                  y={MARGIN.top}
                  width={band}
                  height={plotHeight}
                  fill="transparent"
                  onMouseEnter={() => setHover(i)}
                  onMouseLeave={() => setHover(null)}
                />
              </g>
            );
          })}
        </svg>
      )}
      {hover !== null && (
        <Tooltip x={center(hover)} width={width}>
          <div className="font-semibold text-neutral-900">
            Tháng {data[hover].month}/{data[hover].year}
            {hover === last && <span className="font-normal text-neutral-500"> (đến nay)</span>}
          </div>
          <div className="text-neutral-700">{formatNumber(data[hover].minutes)} phút đi trễ</div>
          <div className="text-neutral-500">{data[hover].count} lượt đi trễ</div>
        </Tooltip>
      )}
    </div>
  );
};
