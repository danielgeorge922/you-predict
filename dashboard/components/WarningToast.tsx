import React from "react";

const WarningToast = () => {
  return (
    <div className="p-4 bg-yellow-100  text-yellow-700 rounded-xl text-xs shadow-sm">
      <strong>⚠️ Warning!</strong> Data may not be fresh and the model cannot
      retrain automatically at the moment.
    </div>
  );
};

export default WarningToast;
