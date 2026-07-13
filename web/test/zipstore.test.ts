import { describe, expect, it } from "vitest";
import { buildZip } from "../src/core/zipstore";

describe("zipstore (store-only ZIP)", () => {
  it("produces a valid EOCD and local/central signatures", () => {
    const zip = buildZip([
      { name: "a.txt", data: new TextEncoder().encode("hello") },
      { name: "b.bin", data: new Uint8Array([1, 2, 3, 4]) },
    ]);
    const dv = new DataView(zip.buffer);
    expect(dv.getUint32(0, true)).toBe(0x04034b50); // first local header
    // EOCD at the tail
    const eocd = zip.length - 22;
    expect(dv.getUint32(eocd, true)).toBe(0x06054b50);
    expect(dv.getUint16(eocd + 10, true)).toBe(2); // total entries
  });

  it("stores payloads uncompressed and recoverable", () => {
    const payload = new Uint8Array([9, 8, 7, 6, 5]);
    const zip = buildZip([{ name: "x.3ds", data: payload }]);
    // method 0 (store): compressed size == uncompressed size
    const dv = new DataView(zip.buffer);
    expect(dv.getUint16(8, true)).toBe(0); // method store
    expect(dv.getUint32(18, true)).toBe(payload.length);
    expect(dv.getUint32(22, true)).toBe(payload.length);
    // payload bytes appear right after the local header + name
    const nameLen = dv.getUint16(26, true);
    const start = 30 + nameLen;
    expect(Array.from(zip.slice(start, start + payload.length))).toEqual(Array.from(payload));
  });
});
