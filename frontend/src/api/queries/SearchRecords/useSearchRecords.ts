import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  SearchRecordsDocument,
  type SearchRecordsQuery,
  type SearchRecordsQueryVariables,
} from "./operation.generated";

interface UseSearchRecordsReturnType {
  triggerAPI: (variables: SearchRecordsQueryVariables) => void;
  data: SearchRecordsQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/**
 * Epic 005, FR-22: the records view's search. As useGetRecords, the caller
 * reacts to `data` and passes it to this operation's responseHandler.
 */
const useSearchRecords = (): UseSearchRecordsReturnType => {
  const [searchRecords, { data, networkStatus, error }] = useLazyQuery<
    SearchRecordsQuery,
    SearchRecordsQueryVariables
  >(SearchRecordsDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: SearchRecordsQueryVariables): void => {
    searchRecords({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useSearchRecords;
