import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MetricCard from "../MetricCard";

describe("MetricCard", () => {
  it("displays label and value", () => {
    render(<MetricCard label="Win Rate" value="56%" />);
    expect(screen.getByText("Win Rate")).toBeInTheDocument();
    expect(screen.getByText(/56%/)).toBeInTheDocument();
  });

  it("applies positive styling", () => {
    render(<MetricCard label="P&L" value="+₹1,000 ▲" positive={true} />);
    const el = screen.getByLabelText("P&L: +₹1,000 ▲");
    expect(el.className).toContain("emerald");
  });

  it("applies negative styling", () => {
    render(<MetricCard label="P&L" value="-₹500 ▼" positive={false} />);
    const el = screen.getByLabelText("P&L: -₹500 ▼");
    expect(el.className).toContain("red");
  });
});
