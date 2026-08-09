import PropTypes from "prop-types";
import Link from "next/link";

/**
 * OriginalDocuments
 * オリジナル資料
 */
export default function OriginalDocuments(props) {
  const urlPrefix = `/positions/${props.positionId}/${props.companyId}`;

  const originalDocuments = props.originalDocumentImtList.map(
    (originalDocument) => {
      return (
        <li key={originalDocument.get("ID")}>
          <Link
            href={`${urlPrefix}/originalDocument/${originalDocument.get("ID")}`}
          >
            <a>{originalDocument.get("Label")}</a>
          </Link>
        </li>
      );
    },
  );

  return <ul>{originalDocuments}</ul>;
}

OriginalDocuments.propTypes = {
  positionId: PropTypes.number.isRequired,
  companyId: PropTypes.number.isRequired,
  originalDocumentImtList: PropTypes.object.isRequired,
};
