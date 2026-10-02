import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useRecordSearchEvent from "../../../../api/mutations/RecordSearchEvent/useRecordSearchEvent";
import { useResponseHandler } from "../../../../api/queries/GetRelatedRecords/responseHandler";
import useGetRelatedRecords from "../../../../api/queries/GetRelatedRecords/useGetRelatedRecords";
import { API_FAILED } from "../../../../constants/apiConstants";
import type { RecordRow } from "../../../../stores/RecordsStore";
import { useStore } from "../../../../stores/StoreProvider";
import type { RecordType } from "../../../../../types.generated";
import RelatedRecords, { type RelatedStateType } from "../../components/RelatedRecords";
import { recordPath } from "../../utils/recordPath";

interface RelatedRecordsControllerProps {
  recordType: RecordType;
  id: string;
}

/**
 * Epic 005, FR-25 to FR-28: loads one detail's related list when the detail
 * opens, every time, and never stores it beyond this session (FR-27). The
 * detail renders without waiting for it.
 */
const RelatedRecordsController = (props: RelatedRecordsControllerProps): ReactElement => {
  const { recordType, id } = props;
  const store = useStore();
  const navigate = useNavigate();
  const { triggerAPI, data, apiStatus } = useGetRelatedRecords();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: recordSearchEvent } = useRecordSearchEvent();
  const key = `${recordType}:${id}`;

  useEffect(() => {
    triggerAPI({ recordType, id });
    // triggerAPI is left out on purpose, per repo-rules.md §13.4.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    if (!data) return;
    handleResponse({ data, onRelatedLoaded: (records) => store.related.setRelated(key, records) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const rows = store.related.getRelated(key);
  let state: RelatedStateType = "LIST";
  if (apiStatus === API_FAILED) state = "ERROR";
  else if (rows === null) state = "LOADING";
  else if (rows.length === 0) state = "EMPTY";

  const handleOpenRow = (row: RecordRow, position: number): void => {
    recordSearchEvent({ kind: "RELATED_OPENED", position });
    navigate(recordPath(row));
  };

  return (
    <RelatedRecords
      state={state}
      rows={rows ?? []}
      onOpenRow={handleOpenRow}
      onRetry={() => triggerAPI({ recordType, id })}
    />
  );
};

export default observer(RelatedRecordsController);
