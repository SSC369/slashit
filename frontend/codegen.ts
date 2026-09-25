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
    },
    // Vite/esbuild's isolatedModules-style transpilation forbids runtime
    // `enum` declarations (tsconfig's erasableSyntaxOnly). Union string
    // literal types are erasable and carry the same values.
    enumsAsTypes: true,
  },
};

export default config;
