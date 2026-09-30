import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetRelatedRecordsDocument,
  type GetRelatedRecordsQuery,
  type GetRelatedRecordsQueryVariables,
} from "./operation.generated";

interface UseGetRelatedRecordsReturnType {
  triggerAPI: (variables: GetRelatedRecordsQueryVariables) => void;
  data: GetRelatedRecordsQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Epic 005, FR-25 to FR-28: a detail's related list, its own query so it
 * never holds up the detail. The caller reacts to `data`. */
const useGetRelatedRecords = (): UseGetRelatedRecordsReturnType => {
  const [getRelatedRecords, { data, networkStatus, error }] = useLazyQuery<
    GetRelatedRecordsQuery,
    GetRelatedRecordsQueryVariables
  >(GetRelatedRecordsDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetRelatedRecordsQueryVariables): void => {
    getRelatedRecords({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetRelatedRecords;
