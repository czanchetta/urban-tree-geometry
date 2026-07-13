// Unit tests for the faithful height core (mirror the Python pytest units).
import { describe, it, expect } from "vitest";
import {
  roundToStep, roundDecimal, dbhFromPerimeter, heightFromDbh, heightBand, UnitError,
} from "../src/core/calculations";

// Note: exhaustive Python<->TS numeric agreement is asserted by the 135-case
// equivalence fixture (equivalence.test.ts). These are focused sanity checks.

describe("roundToStep (half away from zero)", () => {
  it("rounds to 0.5 grid", () => {
    expect(roundToStep(1.24)).toBe(1.0);
    expect(roundToStep(1.25)).toBe(1.5);
    expect(roundToStep(1.75)).toBe(2.0);
    expect(roundToStep(2.25)).toBe(2.5);
  });
});

describe("roundDecimal (round-half-to-even, matches Python round)", () => {
  it("rounds non-ties correctly", () => {
    expect(roundDecimal(9.549, 1)).toBe(9.5);
    expect(roundDecimal(0.09549, 4)).toBe(0.0955);
    expect(roundDecimal(8.594, 2)).toBe(8.59);
    expect(roundDecimal(8.596, 2)).toBe(8.6);
  });
  it("breaks exact binary ties to even (like Python)", () => {
    expect(roundDecimal(5.625, 2)).toBe(5.62); // tie -> even (2)
    expect(roundDecimal(0.125, 2)).toBe(0.12); // tie -> even (2)
    expect(roundDecimal(0.375, 2)).toBe(0.38); // tie -> even (8)
    expect(roundDecimal(2.5, 0)).toBe(2);
    expect(roundDecimal(3.5, 0)).toBe(4);
  });
  it("normalises -0 to 0", () => {
    expect(Object.is(roundDecimal(-0.0001, 2), 0)).toBe(true);
  });
});

describe("dbhFromPerimeter", () => {
  it("computes P/pi", () => {
    expect(dbhFromPerimeter(Math.PI)).toBeCloseTo(1.0, 12);
  });
  it("rejects missing / non-positive", () => {
    expect(() => dbhFromPerimeter(null)).toThrow(UnitError);
    expect(() => dbhFromPerimeter(0)).toThrow(UnitError);
    expect(() => dbhFromPerimeter(-5)).toThrow(UnitError);
  });
});

describe("heightFromDbh", () => {
  it("reproduces a known workbook value (H_inf=25,k=45,P=300)", () => {
    const dbh = dbhFromPerimeter(300);
    expect(heightFromDbh(dbh, 25, 45)).toBe(22.0);
  });
  it("rejects invalid parameters", () => {
    expect(() => heightFromDbh(10, 1.0, 45)).toThrow();
    expect(() => heightFromDbh(10, 25, 0)).toThrow();
    expect(() => heightFromDbh(0, 25, 45)).toThrow(UnitError);
  });
});

describe("heightBand", () => {
  it("floors lower bound at 2 m and rounds to 0.5", () => {
    expect(heightBand(21.5)).toEqual([17.0, 26.0]);
    expect(heightBand(2.0)).toEqual([2.0, 2.5]);
  });
});
