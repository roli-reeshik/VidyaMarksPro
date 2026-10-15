import React from "react";
import { Sem1Marksheet } from "./Sem1Marksheet";
import { Sem2Marksheet } from "./Sem2Marksheet";
import { Sem3Marksheet } from "./Sem3Marksheet";
import { Sem4Marksheet } from "./Sem4Marksheet";
import { Sem5Marksheet } from "./Sem5Marksheet";
import { Sem6Marksheet } from "./Sem6Marksheet";
import { Sem7Marksheet } from "./Sem7Marksheet";
import { Sem8Marksheet, Sem8MarksheetProps } from "./Sem8Marksheet";
import { MarksheetBaseProps } from "./shared";

export {
  Sem1Marksheet,
  Sem2Marksheet,
  Sem3Marksheet,
  Sem4Marksheet,
  Sem5Marksheet,
  Sem6Marksheet,
  Sem7Marksheet,
  Sem8Marksheet,
};

export * from "./shared";

export interface MarksheetRendererProps extends MarksheetBaseProps {
  semesterNumber: number;
  cumulativeHistory?: Sem8MarksheetProps["cumulativeHistory"];
  finalCgpa?: number;
  finalClassification?: string;
}

/**
 * Dynamic Dispatcher Component:
 * Selects and renders the appropriate semester marksheet component based on semesterNumber (1 to 8).
 */
export const MarksheetRenderer: React.FC<MarksheetRendererProps> = ({
  semesterNumber,
  ...props
}) => {
  switch (semesterNumber) {
    case 1:
      return <Sem1Marksheet {...props} />;
    case 2:
      return <Sem2Marksheet {...props} />;
    case 3:
      return <Sem3Marksheet {...props} />;
    case 4:
      return <Sem4Marksheet {...props} />;
    case 5:
      return <Sem5Marksheet {...props} />;
    case 6:
      return <Sem6Marksheet {...props} />;
    case 7:
      return <Sem7Marksheet {...props} />;
    case 8:
      return <Sem8Marksheet {...props} />;
    default:
      return <Sem1Marksheet {...props} />;
  }
};

export default MarksheetRenderer;
