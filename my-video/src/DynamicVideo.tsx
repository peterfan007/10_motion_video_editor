import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  Video,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/NotoSansKR";

// Load Noto Sans KR font for Korean subtitles
const { fontFamily } = loadFont("normal", {
  weights: ["700"],
});

// Define schema for parameterized rendering
export const dynamicVideoSchema = z.object({
  folderName: z.string(),
  sceneData: z.array(
    z.object({
      scene_id: z.number(),
      start: z.number(),
      end: z.number(),
      duration_frames: z.number(),
      has_video: z.boolean().optional(),
      text_blocks: z.array(
        z.object({
          text: z.string(),
          start: z.number(),
          end: z.number(),
        })
      ),
    })
  ),
  durationInFrames: z.number(),
});

type DynamicVideoProps = z.infer<typeof dynamicVideoSchema>;

// Subtitle Overlay component
const SubtitleOverlay: React.FC<{
  sceneData: DynamicVideoProps["sceneData"];
}> = ({ sceneData }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // Flatten all text blocks across all scenes to check against global time
  const allBlocks = sceneData.flatMap((scene) => scene.text_blocks);

  // Find the active text block for the current timestamp
  const currentBlock = allBlocks.find(
    (block) => currentTime >= block.start && currentTime <= block.end
  );

  if (!currentBlock) return null;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        paddingBottom: "80px",
        pointerEvents: "none",
        zIndex: 100,
      }}
    >
      <div
        style={{
          fontFamily,
          textShadow: "0 2px 8px rgba(0,0,0,0.9)",
          backgroundColor: "rgba(0, 0, 0, 0.65)",
          color: "#ffffff",
          fontSize: "42px",
          fontWeight: "bold",
          textAlign: "center",
          padding: "16px 36px",
          maxWidth: "80%",
          lineHeight: "1.5",
          borderRadius: "16px",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
        }}
      >
        {currentBlock.text}
      </div>
    </AbsoluteFill>
  );
};

// Scene Video Component with graceful fallback
const SceneVideo: React.FC<{
  folderName: string;
  sceneId: number;
  hasVideo: boolean;
}> = ({ folderName, sceneId, hasVideo }) => {
  const videoSrc = staticFile(`outputs/${folderName}/scene${sceneId}.mp4`);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        background: "linear-gradient(135deg, #1e1e2f 0%, #11111b 100%)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Dynamic Scene Video - rendered only if it exists in the folder */}
      {hasVideo ? (
        <Video
          src={videoSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
          muted
          loop
        />
      ) : null}

      {/* Decorative scene indicator (visible if video is not loaded or for debugging) */}
      <div
        style={{
          position: "absolute",
          top: "30px",
          left: "30px",
          color: "rgba(255, 255, 255, 0.4)",
          fontFamily,
          fontSize: "20px",
          fontWeight: 500,
          backgroundColor: "rgba(0, 0, 0, 0.3)",
          padding: "6px 14px",
          borderRadius: "8px",
          backdropFilter: "blur(4px)",
        }}
      >
        Scene {sceneId}
      </div>
    </div>
  );
};

export const DynamicVideo: React.FC<DynamicVideoProps> = ({
  folderName,
  sceneData,
}) => {
  const audioSrc = staticFile(`outputs/${folderName}/output_1.2x.wav`);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* 1. Combined Background Audio Track */}
      {folderName && <Audio src={audioSrc} />}

      {/* 2. Sequence layer for each scene's video */}
      {sceneData.map((scene, index) => {
        // 이전 씬의 end 프레임을 시작점으로 잡아서 1프레임의 빈 틈도 없도록Contiguous하게 프레임 계산
        const startFrame = index === 0 
          ? 0 
          : Math.round(sceneData[index - 1].end * 30);
        
        const endFrame = Math.round(scene.end * 30);
        const duration = endFrame - startFrame;

        return (
          <Sequence
            key={scene.scene_id}
            from={startFrame}
            durationInFrames={duration}
          >
            <SceneVideo
              folderName={folderName}
              sceneId={scene.scene_id}
              hasVideo={scene.has_video || false}
            />
          </Sequence>
        );
      })}

      {/* 3. Global Subtitles Overlay */}
      <SubtitleOverlay sceneData={sceneData} />
    </AbsoluteFill>
  );
};
