/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type SignInInput = {
  email: string;
  password: string;
};

export type SignInMutationVariables = Exact<{
  input: Types.SignInInput;
}>;


export type SignInMutation = { signIn:
    | { __typename: 'AccountLocked', message: string, retryAfter: string | null }
    | { __typename: 'AccountNotVerified', message: string }
    | { __typename: 'AuthProviderUnavailable', message: string }
    | { __typename: 'InvalidCredentials', message: string }
    | { __typename: 'SignedIn', accessToken: string, refreshToken: string, expiresIn: number }
   };


export const SignInDocument = gql`
    mutation SignIn($input: SignInInput!) {
  signIn(input: $input) {
    __typename
    ... on SignedIn {
      accessToken
      refreshToken
      expiresIn
    }
    ... on InvalidCredentials {
      message
    }
    ... on AccountLocked {
      message
      retryAfter
    }
    ... on AccountNotVerified {
      message
    }
    ... on AuthProviderUnavailable {
      message
    }
  }
}
    `;