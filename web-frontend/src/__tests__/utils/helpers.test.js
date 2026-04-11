import {
  calcPercentChange,
  copyToClipboard,
  debounce,
  deepClone,
  formatAddress,
  formatCurrency,
  formatDate,
  formatLargeNumber,
  formatTokenAmount,
  generateId,
  isEmpty,
  isValidAddress,
  truncateText,
} from "../../utils/helpers";

describe("helpers utilities", () => {
  describe("formatAddress", () => {
    test("formats a full address correctly", () => {
      expect(formatAddress("0x1234567890abcdef1234567890abcdef12345678")).toBe(
        "0x1234...5678"
      );
    });
    test("returns empty string for falsy input", () => {
      expect(formatAddress(null)).toBe("");
      expect(formatAddress(undefined)).toBe("");
      expect(formatAddress("")).toBe("");
    });
  });

  describe("formatTokenAmount", () => {
    test("formats a BigInt token amount", () => {
      const amount = BigInt("1500000000000000000"); // 1.5 ETH
      const result = formatTokenAmount(amount, 18);
      expect(result).toBe("1.5");
    });
    test("formats zero amount", () => {
      expect(formatTokenAmount(BigInt(0), 18)).toBe("0");
    });
    test("returns 0 on error", () => {
      expect(formatTokenAmount("not-a-number", 18)).toBe("0");
    });
  });

  describe("formatDate", () => {
    test("formats a unix timestamp into a readable date", () => {
      const result = formatDate(0);
      expect(result).toContain("1970");
    });
    test("returns a string", () => {
      expect(typeof formatDate(1700000000)).toBe("string");
    });
  });

  describe("isValidAddress", () => {
    test("returns true for valid Ethereum address", () => {
      expect(isValidAddress("0x1234567890abcdef1234567890abcdef12345678")).toBe(true);
    });
    test("returns false for invalid address", () => {
      expect(isValidAddress("not-an-address")).toBe(false);
    });
    test("returns false for null", () => {
      expect(isValidAddress(null)).toBe(false);
    });
    test("returns false for short address", () => {
      expect(isValidAddress("0x1234")).toBe(false);
    });
  });

  describe("copyToClipboard", () => {
    test("returns true on success", async () => {
      Object.assign(navigator, {
        clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
      });
      const result = await copyToClipboard("hello");
      expect(result).toBe(true);
    });
    test("returns false on failure", async () => {
      Object.assign(navigator, {
        clipboard: { writeText: jest.fn().mockRejectedValue(new Error("fail")) },
      });
      const result = await copyToClipboard("hello");
      expect(result).toBe(false);
    });
  });

  describe("debounce", () => {
    jest.useFakeTimers();
    test("calls function after delay", () => {
      const fn = jest.fn();
      const debounced = debounce(fn, 300);
      debounced("arg1");
      expect(fn).not.toHaveBeenCalled();
      jest.runAllTimers();
      expect(fn).toHaveBeenCalledWith("arg1");
    });
    test("only calls once when invoked multiple times rapidly", () => {
      const fn = jest.fn();
      const debounced = debounce(fn, 300);
      debounced();
      debounced();
      debounced();
      jest.runAllTimers();
      expect(fn).toHaveBeenCalledTimes(1);
    });
  });

  describe("formatLargeNumber", () => {
    test("formats millions", () => {
      expect(formatLargeNumber(2500000)).toBe("2.50M");
    });
    test("formats thousands", () => {
      expect(formatLargeNumber(1500)).toBe("1.50K");
    });
    test("formats small numbers as-is", () => {
      expect(formatLargeNumber(999)).toBe("999");
    });
  });

  describe("formatCurrency", () => {
    test("formats a number as USD currency", () => {
      expect(formatCurrency(1234.5)).toBe("$1,234.50");
    });
    test("returns $0.00 for NaN", () => {
      expect(formatCurrency("abc")).toBe("$0.00");
    });
    test("formats zero", () => {
      expect(formatCurrency(0)).toBe("$0.00");
    });
  });

  describe("generateId", () => {
    test("returns a non-empty string", () => {
      const id = generateId();
      expect(typeof id).toBe("string");
      expect(id.length).toBeGreaterThan(0);
    });
    test("generates unique ids", () => {
      const ids = new Set(Array.from({ length: 100 }, generateId));
      expect(ids.size).toBe(100);
    });
  });

  describe("isEmpty", () => {
    test("returns true for empty object", () => {
      expect(isEmpty({})).toBe(true);
    });
    test("returns false for non-empty object", () => {
      expect(isEmpty({ key: "value" })).toBe(false);
    });
    test("returns true for null", () => {
      expect(isEmpty(null)).toBe(true);
    });
  });

  describe("deepClone", () => {
    test("creates a deep copy", () => {
      const obj = { a: { b: 1 } };
      const clone = deepClone(obj);
      clone.a.b = 99;
      expect(obj.a.b).toBe(1);
    });
  });

  describe("truncateText", () => {
    test("truncates long text", () => {
      const result = truncateText("Hello World", 5);
      expect(result).toBe("Hello...");
    });
    test("does not truncate short text", () => {
      expect(truncateText("Hi", 50)).toBe("Hi");
    });
    test("handles null/undefined", () => {
      expect(truncateText(null)).toBeNull();
    });
  });

  describe("calcPercentChange", () => {
    test("calculates positive change", () => {
      expect(calcPercentChange(110, 100)).toBe(10);
    });
    test("calculates negative change", () => {
      expect(calcPercentChange(90, 100)).toBe(-10);
    });
    test("returns 0 when previous is 0", () => {
      expect(calcPercentChange(100, 0)).toBe(0);
    });
  });
});
