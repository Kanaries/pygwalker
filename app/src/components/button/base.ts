import React from 'react';

export interface ButtonBaseProps {
    onClick: (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
    text: string;
    disabled?: boolean;
    className?: string;
}