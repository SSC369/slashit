import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "./schema.graphql",
  documents: ["src/api/**/operation.graphql", "src/fragments/**/*.graphql"],
  generates: {
    "src/api/": {
      preset: "near-operation-file",
      presetConfig: {
        extension: ".generated.ts",
        baseTypesPath: "../../types.generated.ts",
      },
      plugins: ["typescript-operations", "typescript-react-apollo"],
      config: {
        withHooks: false,
        withMutationFn: false,
        withResultType: false,
        withMutationOptionsType: false,
        avoidOptionals: { field: true },
      },
    },
    "types.generated.ts": {
      plugins: ["typescript"],
    },
  },
  config: {
    scalars: {
      DateTime: "string",
      Date: "string",
      // Whole paise as a decimal string (006 index §4): a number would lose
      // precision past 2^53, so amounts stay strings until summed as BigInt.
      Paise: "string",
    },
    // Vite/esbuild's isolatedModules-style transpilation forbids runtime
    // `enum` declarations (tsconfig's erasableSyntaxOnly). Union string
    // literal types are erasable and carry the same values.
    enumsAsTypes: true,
  },
};

export default config;
