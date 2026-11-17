/** Rendering of truthfulness-critical components (null handling, provisional banner, gate states). SYNTHETIC inputs only. */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Gate } from "@/components/Gate";
import { ProvisionalBanner, UnavailableValue, Value } from "@/components/ui";

afterEach(cleanup);

describe("SYNTHETIC: null rendering", () => {
  it("renders null/undefined/empty as an explicit Unavailable badge", () => {
    render(
      <ul>
        <li data-testid="a"><Value v={null} /></li>
        <li data-testid="b"><Value v={undefined} /></li>
        <li data-testid="c"><Value v="" /></li>
        <li data-testid="d"><Value v="Shop Now" /></li>
        <li data-testid="e"><Value v={0} /></li>
      </ul>,
    );
    expect(screen.getByTestId("a").textContent).toBe("Unavailable");
    expect(screen.getByTestId("b").textContent).toBe("Unavailable");
    expect(screen.getByTestId("c").textContent).toBe("Unavailable");
    expect(screen.getByTestId("d").textContent).toBe("Shop Now");
    expect(screen.getByTestId("e").textContent).toBe("0"); // zero is a value, not missing
  });
  it("UnavailableValue explains itself", () => {
    render(<UnavailableValue reason="clustering not run" />);
    expect(screen.getByText("Unavailable").getAttribute("title")).toBe("clustering not run");
  });
});

describe("SYNTHETIC: provisional banner", () => {
  it("states that the data is provisional and not for citation", () => {
    render(<ProvisionalBanner />);
    const banner = screen.getByRole("alert");
    expect(banner.textContent).toMatch(/Provisional data/);
    expect(banner.textContent).toMatch(/not for citation/);
  });
});

describe("SYNTHETIC: Gate", () => {
  it("shows loading, then the empty-state reason when a file is missing, and never the children", () => {
    const { rerender } = render(
      <Gate loading result={undefined} title="No data">{() => <p>child</p>}</Gate>,
    );
    expect(screen.getByRole("status").textContent).toMatch(/Loading/);
    rerender(
      <Gate loading={false} result={{ status: "missing", data: null, reason: "clusters.json has not been generated yet." }} title="Clusters not available">
        {() => <p>child</p>}
      </Gate>,
    );
    expect(screen.getByText("Clusters not available")).toBeTruthy();
    expect(screen.getByText(/has not been generated/)).toBeTruthy();
    expect(screen.queryByText("child")).toBeNull();
  });
  it("labels unreadable files as errors", () => {
    render(<Gate loading={false} result={{ status: "error", data: null, reason: "bad" }} title="Ads">{() => <p>child</p>}</Gate>);
    expect(screen.getByText("Ads: data could not be read")).toBeTruthy();
  });
  it("renders children with data when ok", () => {
    render(<Gate loading={false} result={{ status: "ok", data: 3, reason: null }} title="x">{(n) => <p>value {n}</p>}</Gate>);
    expect(screen.getByText("value 3")).toBeTruthy();
  });
});
