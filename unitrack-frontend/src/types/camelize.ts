/* eslint-disable @typescript-eslint/no-explicit-any */
// Convert snake_case to camelCase
const toCamel = (str: string) =>
  str.replace(/([-_][a-z])/g, (group) =>
    group.toUpperCase().replace("-", "").replace("_", "")
  );

// Recursively convert object keys
export const camelize = (input: any): any => {
  if (Array.isArray(input)) {
    return input.map((item) => camelize(item));
  }

  if (input !== null && typeof input === "object") {
    return Object.keys(input).reduce((acc: any, key: string) => {
      const camelKey = toCamel(key);
      acc[camelKey] = camelize(input[key]);
      return acc;
    }, {});
  }

  return input;
};
