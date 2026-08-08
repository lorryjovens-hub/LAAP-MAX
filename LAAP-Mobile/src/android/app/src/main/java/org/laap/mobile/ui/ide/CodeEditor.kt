package org.laap.mobile.ui.ide

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.laap.mobile.ui.markdown.SyntaxHighlighter
import org.laap.mobile.ui.terminal.JetBrainsMonoFontFamily

/**
 * Lightweight IDE-style code editor built on Compose [BasicTextField].
 *
 * MVP scope — intentionally minimal:
 * - JetBrains Mono monospace font (matches the terminal)
 * - Line-number gutter (toggleable)
 * - Regex syntax highlight via the existing [SyntaxHighlighter]
 * - Single-file, no tabs (caller manages open-file state)
 * - No autocomplete / LSP / find-replace / multi-cursor
 *
 * The component is uncontrolled-ish: caller owns `code` and `onCodeChange`,
 * which keeps the save flow simple (caller writes to disk when the user
 * taps Save — see [org.laap.mobile.ui.ide.ProjectWorkspaceScreen]).
 */
@Composable
fun CodeEditor(
    code: String,
    onCodeChange: (String) -> Unit,
    languageId: String,
    modifier: Modifier = Modifier,
    showLineNumbers: Boolean = true,
    readOnly: Boolean = false,
) {
    // BasicTextField with a VisualTransformation would be the "Compose way"
    // to do syntax highlight without losing cursor position semantics, but
    // VisualTransformation is fragile with multi-line text and the existing
    // SyntaxHighlighter returns an AnnotatedString directly. Instead we
    // re-highlight on every keystroke into a parallel AnnotatedString and
    // feed it via a custom rendering. The simplest correct approach for
    // MVP: use BasicTextField with a `value: TextFieldValue` and re-render
    // the highlighted text on each change.
    var textFieldValue by remember { mutableStateOf(TextFieldValue(code)) }

    // Sync external `code` updates (e.g. open another file) into the field.
    if (textFieldValue.text != code) {
        textFieldValue = TextFieldValue(code)
    }

    val lineCount = remember(code) { code.count { it == '\n' } + 1 }

    val gutterWidth = when {
        lineCount < 100 -> 28.dp
        lineCount < 1_000 -> 40.dp
        lineCount < 10_000 -> 56.dp
        else -> 72.dp
    }

    Row(modifier = modifier.fillMaxSize()) {
        if (showLineNumbers) {
            LineNumberGutter(
                lineCount = lineCount,
                width = gutterWidth,
                modifier = Modifier
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .verticalScroll(rememberScrollState()),
            )
        }

        BasicTextField(
            value = textFieldValue,
            onValueChange = { v ->
                textFieldValue = v
                onCodeChange(v.text)
            },
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 8.dp, vertical = 4.dp),
            enabled = !readOnly,
            readOnly = readOnly,
            textStyle = TextStyle(
                fontFamily = JetBrainsMonoFontFamily,
                fontSize = 13.sp,
                color = Color(0xFFD4D4D4),
                lineHeight = 18.sp,
            ),
            cursorBrush = SolidColor(MaterialTheme.colorScheme.primary),
            keyboardOptions = KeyboardOptions(
                capitalization = KeyboardCapitalization.None,
                autoCorrectEnabled = false,
            ),
            visualTransformation = remember(languageId) { HighlightTransformation(languageId) },
        )
    }
}

@Composable
private fun LineNumberGutter(
    lineCount: Int,
    width: androidx.compose.ui.unit.Dp,
    modifier: Modifier = Modifier,
) {
    val gutterText = buildString {
        for (i in 1..lineCount) {
            appendLine(i.toString().padStart(4))
        }
    }
    androidx.compose.material3.Text(
        text = gutterText,
        fontFamily = JetBrainsMonoFontFamily,
        fontSize = 11.sp,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = modifier
            .width(width)
            .padding(horizontal = 4.dp, vertical = 4.dp),
    )
}

private class HighlightTransformation(private val languageId: String) : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val highlighted: AnnotatedString = SyntaxHighlighter.highlight(text.text, languageId)
        return TransformedText(highlighted, OffsetMapping.Identity)
    }
}
