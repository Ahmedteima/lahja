import { createContext, useState } from "react";

export const VideoContext = createContext();

export function VideoProvider({ children }) {
const [videoFile, setVideoFile] = useState(null);

return (
    <VideoContext.Provider
    value={{
        videoFile,
        setVideoFile,
    }}
    >
    {children}
    </VideoContext.Provider>
);
}