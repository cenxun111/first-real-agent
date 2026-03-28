import styles from './ApprovalModal.module.css';
import type { PendingTool } from '../types';

interface Props {
  tool: PendingTool;
  onApprove: () => void;
  onReject: () => void;
}

export function ApprovalModal({ tool, onApprove, onReject }: Props) {
  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h2 className={styles.title}>⚠️ Approval Required</h2>
        <p className={styles.desc}>
          Agent wants to execute: <strong className={styles.toolName}>{tool.name}</strong>
        </p>
        <div className={styles.argsBox}>
          <pre>{JSON.stringify(tool.args, null, 2)}</pre>
        </div>
        <div className={styles.actions}>
          <button className={styles.rejectBtn} onClick={onReject}>✕ Reject</button>
          <button className={styles.approveBtn} onClick={onApprove}>✓ Approve</button>
        </div>
      </div>
    </div>
  );
}
