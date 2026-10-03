import type { ReactElement } from "react";

import ShareBar from "../../../components/ShareBar";
import { EXPENSE_CATEGORY_LABEL } from "../../../constants/expenseConstants";
import type { ExpenseSummaryFieldsFragment } from "../../../fragments/ExpenseSummaryFields.generated";
import { formatRupees, shareOf, spokenRupees } from "../../../utils/money";
import * as Styles from "./styles";

const CELLS_PER_ROW = 4;

interface ExpenseSummaryBandProps {
  summary: ExpenseSummaryFieldsFragment;
}

/** `RecordsExpenses`' `.band` (FR-18): the period's total, then up to eight
 * category cells, largest first, in rows of four. */
const ExpenseSummaryBand = (props: ExpenseSummaryBandProps): ReactElement => {
  const { summary } = props;
  const largest = summary.totals[0]?.totalPaise ?? "0";
  const fillerCount = (CELLS_PER_ROW - (summary.totals.length % CELLS_PER_ROW)) % CELLS_PER_ROW;

  return (
    <section className={Styles.bandStyles} aria-label={`Spent, ${summary.label}`}>
      <div className={Styles.bandTotalStyles}>
        <span className={`${Styles.formLabelStyles} ${Styles.bandLabelStyles}`}>Spent · {summary.label}</span>
        <span
          className={`${Styles.bandMoneyStyles} ${Styles.bandTotalAmountStyles}`}
          aria-label={spokenRupees(summary.grandTotalPaise)}
        >
          {formatRupees(summary.grandTotalPaise)}
        </span>
        <span className={Styles.bandCountStyles}>
          {summary.count} {summary.count === 1 ? "expense" : "expenses"}
        </span>
      </div>
      <div className={Styles.bandCellsStyles}>
        {summary.totals.map((total) => (
          <div key={total.category} className={Styles.bandCellStyles}>
            <div className={Styles.bandCellTopStyles}>
              <span>{EXPENSE_CATEGORY_LABEL[total.category]}</span>
              <span
                className={`${Styles.bandMoneyStyles} ${Styles.bandCellAmountStyles}`}
                aria-label={spokenRupees(total.totalPaise)}
              >
                {formatRupees(total.totalPaise)}
              </span>
            </div>
            <ShareBar share={shareOf(total.totalPaise, largest)} />
          </div>
        ))}
        {Array.from({ length: fillerCount }, (_, index) => (
          <div key={`filler-${index}`} className={Styles.bandCellStyles} aria-hidden="true" />
        ))}
      </div>
    </section>
  );
};

export default ExpenseSummaryBand;
