import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import MetricCard from "../MetricCard";

describe("MetricCard", () => {
  it("displays label and value", () => {
    render(<MetricCard label="Win Rate" value="56%" />);
    expect(screen.getByText("Win Rate")).toBeInTheDocument();
    expect(screen.getByText(/56%/)).toBeInTheDocument();
  });

  it("shows positive indicator", () => {
    render(<MetricCard label="P&L" value="$1000" positive={true} />);
    expect(screen.getByText(/▲/)).toBeInTheDocument();
  });

  it("shows negative indicator", () => {
    render(<MetricCard label="P&L" value="-$500" positive={false} />);
    expect(screen.getByText(/▼/)).toBeInTheDocument();
  });
});
