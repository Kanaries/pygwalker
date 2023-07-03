import React from "react";

interface ILoadingIconProps {
  width: number;
  height: number;
}

const loadingIcon: React.FC<ILoadingIconProps> = (props) => {
  return (
    <div style={{ height: props.height, width: props.width, background: "white", padding: "0.4rem" }}>
      <style>
          {`
          .animate-spin {
          position: "absolute";
          color: #fff;
          animation: spin 2s linear infinite;
          }
          @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
          }
          .opacity-25 {
          opacity: 0.25;
          }
          .opacity-75 {
          opacity: 0.75;
          }
          `}
      </style>
      <svg className="animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="rgb(79,79,229)" strokeWidth="4"></circle>
        <path className="opacity-75" fill="rgb(79,79,229)" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  );
};

export default loadingIcon;
